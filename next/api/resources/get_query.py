"""
next_backend Query Resource 
author: Christopher Fernandez, Lalit Jain
Query resource for handling restful querying of experiments in next_backend. 
"""

from flask.ext.restful import Resource, reqparse

import json
import next.utils
import next.broker.broker
import next.api.api_util as api_util
from next.api.api_util import *
from next.api.api_util import APIArgument

from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
keychain = KeyChain()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed. 
post_parser = reqparse.RequestParser(argument_class=APIArgument)

# Custom errors for GET and POST verbs on experiment resource
meta_error = {
    'ExpDoesNotExistError': {
        'message': "No experiment with the specified experiment ID exists.",
        'code': 400,
        'status':'FAIL'
    },
    'QueryGenerationError': {
        'message': "Failed to generate query. Please verify that you have specified the correct application specific query parameters.",
        'code': 400,
        'status': 'FAIL',
    },
}

meta_success = {
    'code': 200,
    'status': 'OK'
}


# Query resource class
class getQuery(Resource):
    def post(self):
        post_parser.add_argument('exp_uid', type=str, required=True)
        post_parser.add_argument('exp_key', type=str, required=True)
        post_parser.add_argument('args', type=dict, required=False)


        # Validate args with post_parser
        args_data = post_parser.parse_args()
        
        # Pull app_id and exp_uid from parsed args
        exp_uid = args_data["exp_uid"]
        exp_key = args_data["exp_key"]
        if not keychain.verify_exp_key(exp_uid, exp_key):
            return api_util.attach_meta({}, api_util.verification_error), 401
            
        # Fetch app_id data from resource manager
        app_id = resource_manager.get_app_id(exp_uid)
        # Standardized participant_uid
        if 'participant_uid' in args_data['args'].keys():
            args_data['args']['participant_uid'] = exp_uid+"_"+args_data['args']['participant_uid']
        # Args from dict to json type
        args_json = json.dumps(args_data)
        # Execute getQuery 
        response_json,didSucceed,message = broker.applyAsync(app_id,exp_uid,"getQuery",args_json)
        
        if not didSucceed:
            return attach_meta({},meta_error['QueryGenerationError'], backend_error=message)
        
        response_dict = json.loads(response_json)
        return attach_meta(response_dict,meta_success), 200
        
            

