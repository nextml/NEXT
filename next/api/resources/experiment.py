from flask import Flask
from flask.ext import restful
from flask.ext.restful import Resource, reqparse, request

import json
import random
import next.utils
import next.broker.broker
from next.api.resource_manager import ResourceManager
from next.api.api_util import *
from next.api.api_util import APIArgument
from next.api.keychain import KeyChain
resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
keychain = KeyChain()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed.
# We use a custom APIArgument class that inherits from the Flask Restful Argument class. See next.api.api_util for details.
exp_parser = reqparse.RequestParser(argument_class=APIArgument)

# Custom errors for GET and POST verbs on experiment resource
meta_error = {
    'ExpDoesNotExistError': {
        'message': "No experiment with the specified experiment ID exists.",
        'code': 400,
        'status': 'FAIL'
    },

    'InitExpError': {
        'message': "Failed to initialize experiment. Please verify that you have specified the correct application specific parameters.",
       'code': 400,
        'status': 'FAIL'
    },
}

meta_success = {
    'code': 200,
    'status': 'OK'
}

class Experiment(Resource):
    def get(self, exp_uid, exp_key):
        get_parser = exp_parser.copy()
        get_parser.add_argument('exp_uid', type=str, required=True )
        get_parser.add_argument('exp_key', type=str, required=True )
        get_parser.add_argument('args', type=dict, required=False )

        if not keychain.verify_exp_key(exp_uid,exp_key):
            return api_util.attach_meta({}, api_util.verification_error), 401

        # Fetch experiment data from resource manager
        experiment = resource_manager.get_experiment(exp_uid)
        algorithms = resource_manager.get_algs_doc_for_exp_uid(exp_uid)
        experiment['algorithms'] = algorithms
        # Throw error if no such experiment exists
        if not experiment:
            return attach_meta({}, meta_error['ExpDoesNotExistError']), 400
        else:
            return attach_meta(experiment, meta_success), 200

    def post(self):
        post_parser = exp_parser.copy()
        post_parser.add_argument('app_id', type=str, required=True)
        post_parser.add_argument('args', type=dict, required=True)
        # Validate args with post_parser
        args_data = post_parser.parse_args()
        app_id = args_data['app_id']
        print app_id
        # Create and set exp_uid
        exp_uid = '%030x' % random.randrange(16**30)
        # Args from dict to json type
        args_json = json.dumps(args_data)
        # Execute initExp through the broker
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'initExp',
                                                             json.dumps(args_data))

        if not didSucceed:
            return attach_meta({}, meta_error['InitExpError'], backend_error=message), 400
        # Create an experiment key and a perm key
        exp_key = keychain.create_exp_key(exp_uid)
        perm_key = keychain.create_perm_key(exp_uid, exp_key)

        return attach_meta({'exp_uid':exp_uid, 'exp_key':exp_key, 'perm_key':perm_key}, meta_success), 200





