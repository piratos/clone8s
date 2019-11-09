import json
import requests

import pika

from base import BaseManager


class NetworkManager(BaseManager):
    def __init__(self, minikublet, rbmqhost="localhost"):
        print("[+] Init NetworkManager")
        super(NetworkManager, self).__init__(minikublet)
        self.cnx = None
        # the queue we listen on is named after the node
        self.queue_name = minikublet.node
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
            self.cnx = pika.BlockingConnection(
                pika.ConnectionParameters(
                    rbmqhost,
                    credentials=credentials
                )
            )
        except pika.exceptions.AMQPConnectionError:
            print("Cannot connect to rabbitMQ at host {}".format(
                rbmq_host))
            return
        # use channel to not load RBMQ
        self.channel = self.cnx.channel()
        self.exchange = self.channel.exchange_declare(
            'mini-api-server',
            exchange_type="direct",
            durable=True
        )
        self.queue = self.channel.queue_declare(
            queue=self.queue_name
        )
        self.channel.queue_bind(
            queue=self.queue_name,
            exchange='mini-api-server',
            routing_key=self.queue_name
        )
        # if first time to run the node then register with apiserver
        # else load the queue messages and start watching

    def post_to_apiserver(self, endpoint, payload):
        url = 'http://{0}:8080/{1}'.format(
            self.k.apiserver,
            endpoint
        )
        print("Sending payload: {}".format(payload))
        r = requests.post(url=url, json=payload)
        return r.text

    def register_to_apiserver(self):
        # registration with apiserver is basically successfully
        # creating a node object in the apiserver
        # post node data to http://apiserver/node/-1
        payload = {
            'name': self.k.node,
            'cert': open(self.k.cert, 'r').read(),
            'ip': self.k.ip
        }
        res = self.post_to_apiserver(
            endpoint='nodes/1',
            payload=payload
        )
        result = json.loads(res)
        if result.get('result') == 'OK':
            print("[+] successfully registered to the apiserver")
            return True
        elif result.get('result') == 'NOK':
            print("[+] Cannot register to the apiserver")
            print("[+] Reason: {}".format(result.get('reason')))
            return False
        print("Unknown error, Registration failed")
        return False

    def get_pod(self, podname):
        url = "http://{0}:8080/pods/{1}".format(
            self.k.apiserver,
            podname)
        res = requests.get(url)
        if res.ok:
            return res.text
        return ""

    def pod_callback(self, channel, method, properties, body):
        """
        Message in pod queue contains action and pod name in json format
        ex: {'action': 'add', 'podname': '<podname>'}
        """
        print('[+] Message received: ', body)
        msg = json.loads(body)
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        # get the pod spec from apiserver
        action = msg['action']
        podspec = self.get_pod(msg['podname'])
        # push to internal kubelet queue on the format
        # (action, podspec, tries)
        self.k.queue.append((action, podspec, 0))

    def receive(self):
        # First recover old events
        # self.channel.basic_recover(
        #     requeue=False,
        #     callback=self.pod_callback
        # )
        # Then subscribe to the queue updates
        print("[+] Start consuming events")
        self.channel.basic_consume(
            self.queue_name,
            self.pod_callback
        )
        self.channel.start_consuming()

    def wait_apiserver(self):
        print("Waiting for apiserver to be up")
        url = "http://{}:8080".format(self.k.apiserver)
        while True:
            try:
                requests.get(url)
                print("Api server running! continuing...")
                break
            except requests.exceptions.ConnectionError:
                continue

    def stop(self):
        self.channel.stop_consuming()
        self.cnx.close()