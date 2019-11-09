import os
import time
from OpenSSL import crypto

import kubelets

from apis import ApiManager
from kubelets import KubeletManager
from watches import WatchManager

class MiniApiServer(object):
    def __init__(self, hostname, ca_file, rbmq_host, etcd_host):
        if not os.path.exists(ca_file):
            raise Exception("CA root cert not provided/accessible")
        _cert = open(ca_file, 'r').read()
        self.ca_cert = crypto.load_certificate(
            crypto.FILETYPE_PEM,
            _cert
        )
        self.hostname = hostname
        self.k_manager = KubeletManager(self)
        self.a_manager = ApiManager(self, etcd_host)
        self.w_manager = WatchManager(self, rbmq_host)

    def try_register_node(self, name, cert, ip):
        print("Starting registration process for node {}".format(name))
        tmp_node = kubelets.Node(name, cert, ip)
        if self.k_manager.verify_node(tmp_node):
            # Create a pod spec queue for this kubelet
            print(
                "Create queue: {0} for kubelet from node {0}".format(
                    name
                )
            )
            self.w_manager.add_queue(name)
            return True
        return False

    def control_loop(self):
        # start serving
        self.a_manager.serve()
        while True:
            time.sleep(20)
            #print("--api sever control loop--")
            #self.w_manager.push_metrics("{'metrics: 120'}")

    def run(self):
        try:
            self.control_loop()
        except KeyboardInterrupt:
            self.k_manager.stop()
            self.a_manager.stop()
            self.w_manager.stop()

if __name__ == '__main__':
    apiserver = MiniApiServer(
        hostname='localhost',
        ca_file='rootCA.crt',
        rbmq_host='localhost',
        etcd_host='localhost'
    )
    apiserver.run()