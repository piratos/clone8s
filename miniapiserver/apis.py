import logging
import multiprocessing

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
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name', type=str, required=True, location='json'
        )
        self.reqparse.add_argument(
            'podspec', type=str, required=True, location='json'
        )
        super(Pod).__init__()


class Node(KResource):
    def __init__(self):
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
        super(Node).__init__()


class ApiManager(object):
    def __init__(self, apiserver):
        print("Init ApiManager")
        self.a = apiserver
        self.app = Flask('MiniApiServer')
        # disable flask stdout as it is a backgrounded process
        #self.app.logger.setLevel(logging.ERROR)
        #log = logging.getLogger('werkzeug')
        #log.setLevel(logging.ERROR)
        # TODO: this does not work look for another solution
        self.api = Api(self.app)
        # register nodes
        self.api.add_resource(Node, '/node/<resource_id>')
        # register pods
        self.api.add_resource(Pod, '/pod/<resource_id>')
        # apisever process
        self.server = multiprocessing.Process(
            target=self.app.run,
            args=(
                self.a.hostname,
                8080,
            ),
            kwargs={
                'threaded': True,
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