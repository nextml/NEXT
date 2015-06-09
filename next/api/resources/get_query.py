"""
next_backend Query Resource 
author: Christopher Fernandez, Lalit Jain
Query resource for handling restful querying of experiments in next_backend. 
"""

from flask import Flask
from flask.ext import restful
from flask.ext.restful import Resource, reqparse

import json
import next.utils
import next.broker.broker
from next.api.api_util import *
from next.api.api_util import APIArgument

from next.api.targetmapper import TargetMapper
from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
targetmapper = TargetMapper() 
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
        """.. http:post:: /experiment/getQuery
        
        Get an experiment query using post. Useful for situations in which a feature vector has to be uploaded.

        **Example request**:

        .. sourcecode:: http

        POST /experiment/getQuery HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu

        {
        	exp_uid: exp_uid,
        
        	args : {
        		features: 
        	}		
   	 }

        **Example response**:

        .. sourcecode:: http
        
        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
        	exp_uid: exp_uid,

        	status: {
        		code: 200,
        		status: OK,
       		},

        	target_indices: {
        		index: 1
        		label: "center"
			flag: 5
       		},

        	alg_uid: ,
		timestamp_query_generated: ,
		participant_uid: 


        }
        
        :<json features: Optional feature vector.

        :>json target_indices: Application specific target indices. 
        :>json alg_uid: 
        :>json timestamp_query_generated:
        :>json participant_uid:

        :statuscode 200: Query successfully returned
        :statuscode 400: Query failed to be generated

        """

        post_parser.add_argument('exp_uid', type=str, required=True)
        post_parser.add_argument('exp_key', type=str, required=True)
        post_parser.add_argument('args', type=dict, required=False)


        # Validate args with post_parser
        args_data = post_parser.parse_args()
        
        # Pull app_id and exp_uid from parsed args
        exp_uid = args_data["exp_uid"]
        exp_key = args_data["exp_key"]
        if not keychain.verify_exp_key(exp_uid, exp_key):
            return api_util.attach_meta({}, api_util.verification_dictionary), 401
            
        # Fetch app_id data from resource manager
        app_id = resource_manager.get_app_id(exp_uid)
        # Standardized participant_uid
        if 'participant_uid' in args_data['args'].keys():
            args_data['args']['participant_uid'] = exp_uid+"_"+args_data['args']['participant_uid']
        # Args from dict to json type
        args_json = json.dumps(args_data["args"])
        # Execute getQuery 
        response_json,didSucceed,message = broker.applyAsync(app_id,exp_uid,"getQuery",args_json)
        
        if not didSucceed:
            return attach_meta({},meta_error['QueryGenerationError'], backend_error=message)
        
        response_dict = eval(response_json)
        for target_index in response_dict["target_indices"]:
            target_index['target'] = targetmapper.get_target_data(exp_uid, target_index["index"])

            
        return attach_meta(response_dict,meta_success), 200
        
            

