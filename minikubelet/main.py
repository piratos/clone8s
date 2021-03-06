import os
import threading
import time
import sys
import yaml

from logs import LogManager
from networks import NetworkManager
from metrics import MetricManager
from pods import PodManager


class MiniKubelet(object):
    def __init__(
        self,
        node,
        cert=None,
        apiserver='localhost',
        manifest_folder='./manifests',
        ip_pool="192.168.5.0/24",
        debug=False):
        print("[+] Start MiniKubelet process")
        self.debug = debug
        self.node = node
        self.ip = '0.0.0.0'
        self.ip_pool = ip_pool
        self.network_name = "{}-bridge".format(self.node)
        self.apiserver = apiserver
        self.cert = cert
        self.exit = False
        self.registered = False
        self.manifest_folder = manifest_folder
        self.watchdog = 0
        self.local_manifests = {}
        # TODO: Use sophisticated queue system
        # queue is a list of (action, podspec, tries)
        self.queue = []
        self.pods = {}
        print("[+] Loading managers")
        self.log_manager = LogManager(self)
        self.metric_manager = MetricManager(self)
        self.network_manager = NetworkManager(self)
        self.pod_manager = PodManager(
            self, network_name=self.network_name, ip_pool=self.ip_pool
        )
        # Halt if docker daemon is not running
        if not self.pod_manager.client:
            print("[!] Docker daemon is not reachable, Halting...")
            sys.exit(1)
        print("[+] MiniKubelet started as node: {}".format(self.node))


    def control_func(self):
        if len(self.queue) > 0:
            print("[+] Reading podspec")
            action, podspec, tries = self.queue.pop(0)
            pod_func = None
            if action == 'add':
                pod_func = self.pod_manager.add_pod
            elif action == 'update':
                pod_func = self.pod_manager.update_pod
            elif action == 'delete':
                pod_func = self.pod_manager.delete_pod
            else:
                return False
            res = None
            try:
                res = pod_func(podspec)
            except Exception:
                if self.debug:
                    raise
                pass
            if not res:
                # enqueue back
                self.queue.append((action, podspec, tries+1))
                return False
            return True
        return False

    def control_loop(self):
        while True:
            if self.exit:
                print("[+] Existing control loop")
                break
            # watch manifest folder
            self.watch_manifests()
            # apply control actions
            res = self.control_func()
            if res:
                print("[+] Control loop ended")
            else:
                pass
            # status the pods
            for name, pod in self.pods.items():
                print("[+] Pod {0} status: {1}".format(
                    name,
                    pod.status())
                )
            time.sleep(5)

    def watch_manifests(self):
        def get_podspec(content):
            spec = yaml.safe_load(content)
            if spec.get('kind') == 'Pod':
                return spec.get('spec', '')
        if not os.path.exists(self.manifest_folder):
            return
        deleted = list(self.local_manifests.keys())
        new_holder = {}
        for file in os.listdir(self.manifest_folder):
            if file.endswith(".yaml"):
                # Build file path
                file_path = os.path.join(
                    self.manifest_folder,
                    file
                )
                # Remove non deleted files
                if file in deleted:
                    deleted.remove(file)
                # Build new local files list cache
                new_holder[file] = get_podspec(
                    open(file_path, 'r').read()
                )
                # Check for added files
                if file not in self.local_manifests:
                    print("[+] Treating added file {}".format(file))
                    self.queue.append(
                        ('add', new_holder[file], 0)
                    )
                    continue
                # Check for modified manifest
                if os.path.getmtime(file_path) > self.watchdog:
                    print("[+] Treating updated file {}".format(file))
                    self.queue.append(
                        ('update', new_holder[file], 0)
                    )
        for file in deleted:
            print("[+] Treating removed file {}".format(file))
            self.queue.append(
                ('delete', self.local_manifests[file], 0)
            )
        # update watchdog and reset file list
        self.watchdog = time.time()
        self.local_manifests = new_holder

    def run(self):
        control_loop_thread = threading.Thread(
            target=self.control_loop
        )
        control_loop_thread.start()
        try:
            # Make sure apiserver is up before progressing
            while True:
                if not self.registered:
                    print("[+] Attempting registration")
                    if self.network_manager.register_to_apiserver():
                        self.network_manager.watch()
                        self.registered = True
                        # when registered a queue with the node name will be created
                        # listen on that queue
                    if self.registered and not self.network_manager.consuming:
                        try:
                            self.network_manager.receive()
                        except:
                            self.network_manager.consuming = False
                time.sleep(1)
                # TODO: check sophisticated event loop framework
        except KeyboardInterrupt:
            self.network_manager.stop()
            print("[+] Waiting for control loop to exit")
            self.exit = True
            control_loop_thread.join()
            print("[+] Exiting main function")


if __name__ == '__main__':
    minikubelet = MiniKubelet(
        node="node-1",
        cert='kubelet.crt',
        apiserver='192.168.0.17',
        manifest_folder='./manifests',
        debug=True
    )
    minikubelet.run()
