"""
next_backend Prediction Resource 
author: Christopher Fernandez, Lalit Jain
Predict resource for handling restful predictions with next_backend. 
"""
from flask import Flask
from flask.ext import restful
from flask.ext.restful import Resource, reqparse
from next.api.api_util import *
from next.api.api_util import APIArgument

import json
import next.utils
import next.broker.broker

from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
keychain = KeyChain()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed. 
post_parser = reqparse.RequestParser(argument_class=APIArgument)

meta_error = {
    'PredictRetrievalError': {
        'message': "No predictions can be retrieved for the specified experiment.",
        'code': 400,
        'status':'FAIL'
    }
}
meta_success = {
    'status':'OK',
    'code':200
}
    
class Predict(Resource):
    def post(self):
        """
        .. http:post:: /experiment/<exp_uid>/predict

        Get stats related to an experiment. For a list of potential plot types and parameters see: .

        **Example request**:
        .. sourcecode:: http

        POST /experiment/<exp_uid> HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu

        {
	        exp_uid: exp_uid,
        	app_id: app_id,
        	args: { }        
            }
        }

        **Example response**:

        .. sourcecode:: http
        
        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {   
        }

        
        :statuscode 200: prediction successfully accessed
        :statuscode 400: prediction retrieval error
        """        
        post_parser.add_argument('exp_uid', type=str, required=True,help="Experiment ID Required.")
        post_parser.add_argument('exp_key', type=str, required=True,help="Experiment ID Required.")
        post_parser.add_argument('args', type=dict, required=True,help="Experiment Args Required.")
        

        # Validate args with post_parser
        args_data = post_parser.parse_args()
        # Pull exp_uid from parsed args_data
        exp_uid = args_data["exp_uid"]
        exp_key = args_data["exp_key"]
        if not keychain.verify_exp_key(exp_uid, exp_key):
            return api_util.attach_meta({}, api_util.verification_dictionary), 401
                    
        # Fetch app_id data from resource manager
        app_id = resource_manager.get_app_id(exp_uid) 
        # Args from dict to json type
        args_json = json.dumps(args_data["args"])
        # Execute getQuery 
        response_json,didSucceed,message = broker.applyAsync(app_id,exp_uid,"predict",args_json)
        
        if didSucceed:
          return meta_attach(response_json,meta_success), 200
        else:
          return meta_attach({},custom_errors['PredictRetrievalError'], backend_error=message),400
