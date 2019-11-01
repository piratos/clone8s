import docker

from base import BaseManager
from pod import PodInterface


# TODO: clean this
# This hack is to avoid initializing the python client for each pod
class Pod(PodInterface):
    def __init__(self, podspec):
        super().__init__(podspec)
        self.client = docker.from_env()


class PodManager(BaseManager):

    def add_pod(self, podspec):
        tmp_pod = Pod(podspec)
        name = tmp_pod.name
        if name in self.k.pods:
            print("{} name is reserved by an existing Pod".format(name))
            print("Cannot add Pod {}".format(name))
            return False
        else:
            print("Starting Pod {}".format(name))
            self.k.pods[name] = tmp_pod
            self.k.pods[name].start()
            print("Pod {} started".format(name))
        return True

    def update_pod(self, podspec):
        tmp_pod = Pod(podspec)
        name = tmp_pod.name
        if name in self.k.pods:
            # Pod needs to be updated delete old and create new
            print("Pod {} going to be updated".format(name))
            self.k.pods[name].stop()
            self.k.pods[name] = tmp_pod
            self.k.pods[name].start()
            print("Pod {} Updated".format(name))
            return True
        else:
            # TODO: handle error properly
            print("Pod {} Does not exist".format(name))
            return False

    def delete_pod(self, podspec):
        tmp_pod = Pod(podspec)
        name = tmp_pod.name
        if not name in self.k.pods:
            print("Pod {} does not exist".format(name))
            # Use python 3.6 f string ?
            print("Cannot delete Pod {}".format(name))
            # The pod does not exist, dont requeue the event
            return True
        print("Pod {} is going to be deleted".format(name))
        self.k.pods[name].stop()
        del self.k.pods[name]
        print("Pod {} deleted".format(name))
        return True
