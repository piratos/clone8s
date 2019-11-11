import pika
import time
from pika.exceptions import AMQPConnectionError

"""
For the watch procedures we use AMQP queues to push and consume events
We use one exchange with multiple queues
- queue stats one (all kubelets produce here)
- queue podBounds one per node(kubelet) (scheduler proceduces here)
- queue replicaset one (horizontal autoscaler produces here)
- queue pod (replicaset controller produces here)
"""

class ApiServerQueue(object):
    def __init__(self, name, desc):
        self.name = name
        self.key = name
        self.description = desc
        self.queue = None

class WatchManager(object):
    def __init__(self, apiserver, rbmq_host='localhost'):
        print("Init WatchManager")
        self.a = apiserver
        self.cnx = None
        self.queue_metrics = ApiServerQueue('metrics', 'metrics')
        self.queue_replicasets = ApiServerQueue('replicasets', 'replicaset')
        self.queue_pods = ApiServerQueue('pods', 'pods')
        # node queues are not created because they re dynamics
        # they should be 
        self.queues = {
            'metrics': self.queue_metrics,
            'replicasets': self.queue_replicasets,
            'pods': self.queue_pods
        }
        self.exchange_name = 'mini-api-server'
        self.exchange = None
        tries = 5
        while tries > 0:
            try:
                self.cnx = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        rbmq_host
                    )
                )
                break
            except AMQPConnectionError:
                print(
                    "[!] Cannot connect to rabbitMQ at host {}".format(
                        rbmq_host
                    )
                )
                tries -= 1
                time.sleep(3)
                print("[+] Tries left: ", tries)
        if not self.cnx:
            return
        self.channel = self.cnx.channel()
        # create exchange
        # Use direct type for hard queue key routing
        self.exchange = self.channel.exchange_declare(
            self.exchange_name,
            exchange_type="direct",
            durable=True
        )
        # create queues
        for queue in self.queues.values():
            tmp_q = self.channel.queue_declare(queue.name)
            queue.queue = tmp_q
            # bind queue to the exchange
            self.channel.queue_bind(
                queue=queue.name,
                exchange=self.exchange_name,
                routing_key=queue.key
            )
    def add_queue(self, queue_name):
        q = ApiServerQueue(name=queue_name, desc=queue_name)
        self.channel.queue_declare(q.name)
        self.queues[q.name] = q
        self.channel.queue_bind(
            queue=q.name,
            exchange=self.exchange_name,
            routing_key=q.key
        )

    def push(self, key, payload):
        return self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=key,
            body=payload
        )

    def push_replicasets(self, message):
        return self.push(self.queue_replicasets.key, message)

    def push_metrics(self, message):
        return self.push(self.queue_metrics.key, message)

    def push_pods(self, message):
        return self.push(self.queue_pods.key, message)

    def stop(self):
        print("Stop WatchManager")
        # close connection
        self.cnx.close()