import json
import requests

import pika

from base import BaseManager


class NetworkManager(BaseManager):
    def __init__(self, minikublet, rbmq_host="localhost"):
        print("[+] Init NetworkManager")
        super(NetworkManager, self).__init__(minikublet)
        self.cnx = None
        self.queue_name = 'metrics'
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
            self.cnx = pika.BlockingConnection(
                pika.ConnectionParameters(
                    rbmq_host,
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
            endpoint='node/1',
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


    def pod_callback(self, channel, method, properties, body):
        print('[+] Message received: ',body)
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

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

    def stop(self):
        self.channel.stop_consuming()
        self.cnx.close()