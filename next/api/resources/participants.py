"""
next_backend Participant Resource 
author: Christopher Fernandez, Lalit Jain
Resource for accessing all participant data related to a resource
"""

'''
example use:
get a tripletMDS query:
curl -X GET http://localhost:8001/api/experiment/[exp_uid]/[exp_key]/participants
'''
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
}

meta_success = {
    'code': 200,
    'status': 'OK'
}

# Participants resource class
class Participants(Resource):
    def get(self, exp_uid, exp_key):
        """
        .. http:get:: /experiment/<exp_uid>/participants

        Get all participant response data associated with a given exp_uid.

        **Example request**:

        .. sourcecode:: http

        GET /experiment/<exp_uid>/participants HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu

        **Example response**:

        .. sourcecode:: http
        
        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
        	participant_responses: [participant_responses]
        	status: {
        		code: 200,
        		status: OK,
       		},
        }
        
        :>json all_participant_responses: list of all participant_responses

        :statuscode 200: Participants responses successfully returned
        :statuscode 400: Participants responses failed to be generated
    	""" 
        if not keychain.verify_exp_key(exp_uid,exp_key):
            return api_util.attach_meta({}, api_util.verification_error), 401

        # Get all participants for exp_uid from resource_manager
        participant_uids = resource_manager.get_participant_uids(exp_uid)
        participant_responses = {}

        # Iterate through list of all participants for specified exp_uid
        for participant in participant_uids:
            response = resource_manager.get_participant_data(participant,exp_uid)
            # Append participant query responses to list
            participant_responses[participant] = response
            
        # Add list of all participant responses into a dictionary for internal communication
        all_participant_responses = {'participant_responses': participant_responses}

        for participant,responses in all_participant_responses["participant_responses"].iteritems():
            for response in responses:
                for target_index in response["target_indices"]:
                    target_index['target'] = targetmapper.get_target_data(exp_uid, target_index["index"])

        # Return participant dict and meta codes
        return attach_meta(all_participant_responses,meta_success), 200
