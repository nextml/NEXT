"""
next_backend Targets Resource 
author: Christopher Fernandez, Lalit Jain
"""
from flask import Flask, request
from flask.ext import restful
from flask.ext.restful import Resource, reqparse

import json
import next.utils
import next.broker.broker
import next.api.api_util as api_util
from next.api.api_util import APIArgument

from next.api.resource_manager import ResourceManager
from next.apps.SimpleTargetManager import SimpleTargetManager

resource_manager = ResourceManager()
targetmapper = SimpleTargetManager()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed.

# Custom errors for GET and POST verbs on experiment resource
meta_error = {
    'message':'Failed to authenticate. Widget is either expired or invalid.',
    'status':'FAIL',
    'code':401
    }

meta_success = {
    'code': 200,
    'status': 'OK'
}

class Targets(Resource):

    def post(self):
        """
        Requires a exp_uid, n, and target_blob to create target map.
        
        USAGE BELOW DEPRECIATED
        Usage: ::\n
        POST {
        'app_id': application id,
        'exp_id': experiment id, 
        'args': application specific keys 
        }
        """
        exp_uid = request.json['exp_uid']

        target_blob = request.json['target_blob']
        current_target_mapping = targetmapper.create_target_mapping(exp_uid, target_blob)
        return api_util.attach_meta({}, meta_success), 200 

    def get(self, exp_uid):
        """
        Requires a exp_uid, n, and target_blob to create target map.
        
        USAGE BELOW DEPRECIATED
        Usage: ::\n
        GET {
        'app_id': application id,
        'exp_id': experiment id, 
        'args': application specific keys 
        }
        """

        current_target_mapping = targetmapper.get_target_mapping(exp_uid)
        return api_util.attach_meta({'target_mapping':current_target_mapping},{'code': 200,'status': 'OK'}), 200
