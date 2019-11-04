import json
import logging
import multiprocessing

import etcd

from flask_restful import Api, abort, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from flask import Flask, jsonify

from flask_restful import reqparse


# TODO: implement a cert authentication
#auth = HTTPBasicAuth()

def authorize():
    # authorize apiserver request
    pass

def check_permission():
    pass

class KResource(Resource):
    method_decorator = {
        "get": [authorize, check_permission],
        "post": [authorize, check_permission]
    }
    #decorators = [auth.login_required]

    def __init__(self, etcd_client, apiserver):
        super(KResource, self).__init__()
        self.etcd = etcd_client
        self.a = apiserver

    def post(self, resource_id):
        args = self.reqparse.parse_args()
        args['id'] = resource_id
        return jsonify(args)

    def put(self, resource_id):
        args = self.reqparse.parse_args()
        args['id'] = resource_id
        return jsonify(args)

    def get(self, resource_id):
        return jsonify({'resource_id': resource_id})



class Pod(KResource):
    def __init__(self, etcd_client, apiserver):
        super(Pod, self).__init__(etcd_client, apiserver)
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name', type=str, required=True, location='json'
        )
        self.reqparse.add_argument(
            'podspec', type=str, required=True, location='json'
        )

class Node(KResource):
    def __init__(self, etcd_client, apiserver):
        super(Node, self).__init__(etcd_client, apiserver)
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name', type=str, required=True, location='json'
        )
        self.reqparse.add_argument(
            'cert', type=str, required=True, location='json'
        )
        self.reqparse.add_argument(
            'ip', type=str, required=True, location='json'
        )

    # TODO: use validation decorator insead
    def post(self, resource_id):
        data = super(Node, self).post(resource_id)
        # try registering a node (check certificate)
        js = data.json
        res = self.a.try_register_node(
            name=js['name'], cert=js['cert'], ip=js['ip']
        )
        if res:
            self.etcd.write(
                '/nodes/{}'.format(js['name']),
                json.dumps(js)
            )
            return jsonify({'result': 'OK', 'reason': ''})
        return jsonify({'result': 'NOK', 'reason': 'Cannot verify node'})


class ApiManager(object):
    def __init__(self, apiserver, etcd_host, etcd_port=None):
        print("Init ApiManager")
        self.a = apiserver
        # Connect to the etcd instance
        self.etcd = None
        try:
            if etcd_port:
                self.etcd = etcd.Client(
                    host=etcd_host,
                    port=etcd_port
                )
            else:
                self.etcd = etcd.Client(host=etcd_host)
        except:
            print("Cannot connect to etcd at host {}".format(etcd_host))
            return
        self.app = Flask('MiniApiServer')
        # disable flask stdout as it is a backgrounded process
        #self.app.logger.setLevel(logging.ERROR)
        #log = logging.getLogger('werkzeug')
        #log.setLevel(logging.ERROR)
        # TODO: this does not work look for another solution
        self.api = Api(self.app)
        # register nodes
        self.api.add_resource(
            Node,
            '/node/<resource_id>',
            resource_class_args=(self.etcd, self.a)
        )
        # register pods
        self.api.add_resource(
            Pod,
            '/pod/<resource_id>',
            resource_class_args=(self.etcd, self.a)
        )
        # apisever process
        self.server = multiprocessing.Process(
            target=self.app.run,
            args=(
                self.a.hostname,
                8080,
            ),
            kwargs={
                'threaded': True,
                'debug': True
            },
            daemon=True,
        )

    def serve(self):
        print("Start listening to apiserver requests")
        self.server.start()

    def stop(self):
        print("Stop ApiManager")
        self.server.terminate()
        # Make sure process existed
        self.server.join()