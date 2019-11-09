import json
import logging
import multiprocessing
import os

import etcd

from flask_restful import Api, abort, Resource, reqparse
from flask_restful import reqparse
from flask_httpauth import HTTPBasicAuth
from flask import Flask, jsonify


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

    def __init__(self, apimanager):
        super(KResource, self).__init__()
        self.api = apimanager

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
    def __init__(self, apimanager):
        super(Pod, self).__init__(apimanager)
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name', type=str, required=True, location='json'
        )
        self.reqparse.add_argument(
            'podspec', type=str, required=True, location='json'
        )

    # TODO: remove the usage of resource id on posts
    def post(self, resource_id):
        data = super(Pod, self).post(resource_id)
        js = data.json
        # TODO: base on UIDs not names
        self.api._etcd_write(
            '/pods/{}'.format(js['name']),
            js['podspec']
        )
        # TODO: replace jsonify() with standard function
        return jsonify({'result': 'OK', 'reason': ''})

    def get(self, resource_id):
        podobj = self.api._etcd_get('/pods/{}'.format(resource_id))
        if podobj:
            return jsonify(podobj)
        return jsonify({})


class Node(KResource):
    def __init__(self, apimanager):
        super(Node, self).__init__(apimanager)
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
        # Dont go intoregistering if node exists
        if self.api._etcd_get('/nodes/{}'.format(js['name'])):
            return jsonify(
                {'result': 'OK', 'reason': 'Node already registered'}
            )
        res = self.api.a.try_register_node(
            name=js['name'], cert=js['cert'], ip=js['ip']
        )
        if res:
            self.api._etcd_write(
                '/nodes/{}'.format(js['name']),
                json.dumps(js)
            )
            return jsonify({'result': 'OK', 'reason': ''})
        return jsonify({'result': 'NOK', 'reason': 'Cannot verify node'})

    def get(self, resource_id):
        node_obj = self.api._etcd_get('/nodes/{}'.format(resource_id))
        if node_obj:
            return jsonify(node_obj)
        return jsonify({})


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
            '/nodes/<resource_id>',
            resource_class_args=(self, )
        )
        # register pods
        self.api.add_resource(
            Pod,
            '/pods/<resource_id>',
            resource_class_args=(self, )
        )
        # apisever process
        os.environ['FLASK_ENV'] = 'development'
        self.server = multiprocessing.Process(
            target=self.app.run,
            args=(
                self.a.hostname,
                8080,
            ),
            kwargs={
                'threaded': True,
                'debug': False
            },
            daemon=True,
        )

    def _etcd_get(self, key):
        """Pythonic get instead of raising exception"""
        try:
            return self.etcd.get(key).value
        except etcd.EtcdKeyNotFound:
            return None

    def _etcd_write(self, key, value):
        return self.etcd.write(key, value)

    def serve(self):
        print("Start listening to apiserver requests")
        self.server.start()

    def stop(self):
        print("Stop ApiManager")
        self.server.terminate()
        # Make sure process existed
        self.server.join()