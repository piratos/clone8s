import docker
import os
import time

from pods import PodInterface

PODSPECADD = "add.podspec"
PODSPECRM = "rm.podspec"

# TODO: clean this
# This hack is to avoid initializing the python client for each pod
class Pod(PodInterface):
    def __init__(self, podspec):
        super().__init__(podspec)
        self.client = docker.from_env()

class MiniKubelet(object):
    def __init__(self, node):
        print("Start MiniKubelet process")
        self.node = node
        # TODO: Use sophisticated queue system
        # queue is a list of (action, podspec, tries)
        self.queue = []
        self.pods = {}

        print("MiniKubelet started as node: {}".format(self.node))

    def add_pod(self, podspec):
        tmp_pod = Pod(podspec)
        name = tmp_pod.name
        if name in self.pods:
            print("{} name is reserved by an existing Pod".format(name))
            print("Cannot add Pod {}".format(name))
            return False
        else:
            print("Starting Pod {}".format(name))
            self.pods[name] = tmp_pod
            self.pods[name].start()
            print("Pod {} started".format(name))
        return True

    def update_pod(self, podspec):
        tmp_pod = Pod(podspec)
        name = tmp_pod.name
        if name in self.pods:
            # Pod needs to be updated delete old and create new
            print("Pod {} going to be updated".format(name))
            self.pods[name].stop()
            self.pods[name] = tmp_pod
            self.pods[name].start()
            print("Pod {} Updated".format(name))
            return True
        else:
            # TODO: handle error properly
            print("Pod {} Does not exist".format(name))
            return False

    def delete_pod(self, podspec):
        tmp_pod = Pod(podspec)
        name = tmp_pod.name
        if not name in self.pods:
            print("Pod {} does not exist".format(name))
            # Use python 3.6 f string ?
            print("Cannot delete Pod {}".format(name))
            return False
        print("Pod {} is going to be deleted".format(name))
        self.pods[name].stop()
        del self.pods[name]
        print("Pod {} deleted".format(name))
        return True

    def control_func(self):
        if len(self.queue) > 0:
            action, podspec, tries = self.queue.pop(0)
            pod_func = None
            if action == 'add':
                pod_func = self.add_pod
            elif action == 'update':
                pod_func = self.update_pod
            elif action == 'delete':
                pod_func = self.delete_pod
            else:
                return False
            if not pod_func(podspec):
                # enqueue back
                self.queue.append((action, podspec, tries+1))
                return False
            return True
        return False

    def control_loop(self):
        while True:
            # apply control actions
            res = self.control_func()
            if res:
                print("Control loop ended -1")
            else:
                print("Control loop ended 0")
            # Read pod spec and enque if any
            if os.path.exists(PODSPECADD):
                podspec = open(PODSPECADD, 'r').read()
                self.queue.append(('add', podspec, 0))
                os.remove(PODSPECADD)
                print("Adding podspec")
            if os.path.exists(PODSPECRM):
                podspec = open(PODSPECRM, 'r').read()
                self.queue.append(('delete', podspec, 0))
                os.remove(PODSPECRM)
                print("Removing podspec")
            # status the pods
            for name, pod in self.pods.items():
                print("Pod {0} statuses: {1}".format(
                    name,
                    pod.status())
                )
            time.sleep(3)


if __name__ == '__main__':
    minikubelet = MiniKubelet(node="node1")
    minikubelet.control_loop()