"""
next_backend Experiment Resource 
author: Christopher Fernandez, Lalit Jain
Experiment resource for handling restful communication with next_backend. 
"""
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
        """
        .. http:get:: /experiment/<exp_uid>/<exp_key>

        Get an experiment initialization configuration from an exp_uid

        **Example request**:

        .. sourcecode:: http

        GET /experiment/<exp_uid> HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu
        
        **Example response**:

        .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        [
        exp_uid: exp_uid,
        meta: {
    code: 200,
    status: OK,
    },
        args: {
    
    }
        ]

        :statuscode 200: no error
        :statuscode 400: there's no experiment   
        """
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
        """
        .. http:post:: /experiment

        Initialize a new experiment. The args input depend on the application type.

        **Example request**:

        .. sourcecode:: http

        POST /experiment HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu

        {
                exp_uid: exp_uid,
        app_id: app_id
        args : {
        params: {
        Application specific params.
        },

        alg_list: [
        {
    		"alg_label": "LilUCB", 
    		"proportion": 0.3333333333333333, 
        	"alg_id": "LilUCB", 
    		"test_alg_label": "LilUCB", 
    		"params": {}
        }
	],
        

    participant_to_algorithm_management: 'one_to_one',
    algorithm_management_mode: 'pure_exploration'
    }
        }

        **Example response**:

        .. sourcecode:: http
        
        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        [
        exp_uid: exp_uid,
        app_id: app_id,
        status: {
    code: 200,
    status: OK,
    }
        ]

        :<json args: Dictionary of options that are application dependent. Must include, params, alg_list, participant_to_algorithm_management, algorithm_management_mode.
        :<json params: Application specific params such as number of arms in multi armed bandit experiments.
        :<json alg_list: A list of algorithm specifications.
        :<json participant_to_algorithm_management: Type of participant management. 
        :<json algorithm_management_mode: Type of algorithm management mode.

        :statuscode 200: experiment successfully created
        :statuscode 400: experiment was not successfully created
        """

        post_parser = exp_parser.copy()
        post_parser.add_argument('app_id', type=str, required=True)
        post_parser.add_argument('args', type=dict, required=True)
        
        # Validate args with post_parser
        args_data = post_parser.parse_args()
        app_id = args_data['app_id']
            
        # Create and set exp_uid
        exp_uid = '%030x' % random.randrange(16**30)
        # Args from dict to json type             
        args_json = json.dumps(args_data['args'])
        # Execute initExp through the broker 
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'initExp',
                                                             args_json)

        if not didSucceed:
            return attach_meta({}, meta_error['InitExpError'], backend_error=message), 400
        
        if not didSucceed:
            raise DatabaseException("Failed to create experiment in database: %s"%(message))
        
        # Create an experiment key and a perm key
        exp_key = keychain.create_exp_key(exp_uid)
        perm_key = keychain.create_perm_key(exp_uid, exp_key)
    
        return attach_meta({'exp_uid':exp_uid, 'exp_key':exp_key, 'perm_key':perm_key}, meta_success), 200
 
        
        
        

