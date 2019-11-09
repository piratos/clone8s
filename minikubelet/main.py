import os
import threading
import time

from logs import LogManager
from networks import NetworkManager
from metrics import MetricManager
from pods import PodManager


class MiniKubelet(object):
    def __init__(self, node, cert=None, apiserver=None, rbmqhost='localhost'):
        print("[+] Start MiniKubelet process")
        self.node = node
        self.ip = '0.0.0.0'
        self.apiserver = apiserver
        self.cert = cert
        self.exit = False
        self.registered = False
        # TODO: Use sophisticated queue system
        # queue is a list of (action, podspec, tries)
        self.queue = []
        self.pods = {}
        print("[+] Loading managers")
        self.log_manager = LogManager(self)
        self.metric_manager = MetricManager(self)
        self.network_manager = NetworkManager(self, rbmqhost=rbmqhost)
        self.pod_manager = PodManager(self)
        print("[+] MiniKubelet started as node: {}".format(self.node))


    def control_func(self):
        if len(self.queue) > 0:
            print("Reading podspec from internal queue")
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
                print("Existing control loop")
                break
            # apply control actions
            res = self.control_func()
            if res:
                print("Control loop ended -1")
            else:
                pass
            # status the pods
            for name, pod in self.pods.items():
                print("Pod {0} statuses: {1}".format(
                    name,
                    pod.status())
                )
            time.sleep(3)
    def run(self):
        control_loop_thread = threading.Thread(
            target=self.control_loop
        )
        control_loop_thread.start()
        # Make sure apiserver is up before progressing
        self.network_manager.wait_apiserver()
        print("[+] Attempting registration")
        self.network_manager.register_to_apiserver()
        # when registered a queue with the node name will be created
        # listen on that queue
        self.network_manager.receive()
        try:
            while True:
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
        apiserver='localhost',
        rbmqhost='localhost'
    )
    minikubelet.run()