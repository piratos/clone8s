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
    def __init__(self, minikubelet, network_name, ip_pool):
        super(PodManager, self).__init__(minikubelet)
        self.client = docker.from_env()
        # TODO: define pod class here
        self.network_name = network_name
        self.ip_pool = ip_pool
        self.network = None
        self.create_network()

    def create_network(self):
        # We cannot lookup by id
        for network in self.client.networks.list():
            if network.name == self.network_name:
                # network exists no need to create it
                self.network = network
                return
        # Config network scheme and create it
        ipam_pool = docker.types.IPAMPool(
            subnet=self.ip_pool
        )
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )
        self.network = self.client.networks.create(
            self.network_name,
            driver="bridge",
            ipam=ipam_config
        )

    def connect_pod(self, pod):
        # Connect the pause container of the pod to the network
        # and assign ip if passed
        # If the pod is asking for an IP then assign it
        self.network.connect(
            pod.parent_container.container,
            ipv4_address=pod.ip
        )
        pod.network = self.network_name

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
            tmp_pod.create()
            self.connect_pod(tmp_pod)
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
            # TODO: check if pod containers can be hot updated
            self.k.pods[name] = tmp_pod
            tmp_pod.create()
            self.connect_pod(tmp_pod)
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
