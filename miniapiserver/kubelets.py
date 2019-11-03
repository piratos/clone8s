import pika
from OpenSSL import crypto


class Node(object):
    def __init__(self, name, cert, ip_addr, hostname=None):
        self.name = name
        self.hostname = name
        if hostname:
            self.hostname = name
        self.cert = cert # the string content of the cert
        self.ip_addr = ip_addr


class KubeletManager(object):
    def __init__(self, apiserver):
        print("Init kubeletManager")
        self.nodes = []
        self.a = apiserver

    def verify_node(self, node):
        # assuming self.a.ca_cert is the crypto.load_certificate
        # node_cert is the string content
        store = crypto.X509Store()
        node_certificate = crypto.load_certificate(crypto.FILETYPE_PEM, node.cert)
        store.add_cert(node_certificate)
        store_context = crypto.X509StoreContext(store, self.a.ca_cert)
        try:
            store_context.validate_certificate()
        except crypto.X509StoreContextError:
            print("Cannot validate certificate for node {}".format(node_name))
            return False
        print("Certificate for node {} validated".format(node_name))
        return True

    def add_node(self, node_name, cert, node_ip_addr, hostname=None):
        node = Node(node_name, cert, node_ip_addr, hostname)
        if self.verify_node(node):
            print("Registered node {} with apiserver".format(node.name))
        else:
            print("Couldnt register node")

    def stop(self):
        print("Stop KubeletManager")