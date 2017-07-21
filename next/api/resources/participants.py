"""
next_backend Participant Resource 
author: Christopher Fernandez, Lalit Jain
Resource for accessing all participant data related to a resource
"""

'''
example use:
get a tripletMDS query:
curl -X GET http://localhost:8001/api/experiment/[exp_uid]/participants
'''
from StringIO import StringIO
import pandas as pd
from flask import Flask, send_file, request, abort
from flask_restful import Resource, reqparse
import traceback

import json
from io import BytesIO 
import zipfile

import next.utils
import next.utils as utils
import next.api.api_util as api_util
from next.api.api_util import APIArgument
from next.api.resource_manager import ResourceManager
from next.database_client.DatabaseAPI import DatabaseAPI
db = DatabaseAPI()
from next.logging_client.LoggerAPI import LoggerAPI
ell = LoggerAPI()

resource_manager = ResourceManager()

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
    def get(self, exp_uid):
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
        true_values ={1, '1', 'True', 'true'}
        zip_true = False
        if 'zip' in request.args.keys():
            zip_true = True if request.args.get('zip') in true_values else False
        csv = False
        if 'csv' in request.args.keys():
            csv = True if request.args.get('csv') in true_values else False

        # Get all participants for exp_uid from resource_manager
        participant_uids = resource_manager.get_participant_uids(exp_uid)
        participant_responses = {}

        # Iterate through list of all participants for specified exp_uid
        for participant in participant_uids:
            response = resource_manager.get_participant_data(participant,
                                                             exp_uid)
            # Append participant query responses to list
            participant_responses[participant] = response

        if csv:
            responses = []
            for participant in participant_uids:
                response = resource_manager.get_participant_data(participant,
                                                                 exp_uid)
                for r in response:
                    responses += [r]

            try:
                response_file = parse_responses(responses)
            except ValueError as e:
                message = str(e)
                message += '\n\n' + str(traceback.format_exc())
                utils.debug_print(message)
                return message

        all_responses = {'participant_responses': participant_responses}
        if zip_true:
            filename, content = ('responses.json', json.dumps(all_responses))
            if request.args.get('csv'):
                filename, content = ('responses.csv', response_file.getvalue())

            zip_responses = BytesIO()
            with zipfile.ZipFile(zip_responses, 'w',
                                 compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(filename, content)
            zip_responses.seek(0)

            return send_file(zip_responses,
                             attachment_filename=filename + '.zip',
                             as_attachment='True')
        else:
            return api_util.attach_meta(all_responses, meta_success), 200

def parse_responses(responses):
    if len(responses) == 0:
        raise ValueError('ERROR: responses have not been recorded')
    exp_uid = responses[0]['exp_uid']
    app_id = resource_manager.get_app_id(exp_uid)
    myApp = utils.get_app(app_id, exp_uid, db, ell).myApp

    if not hasattr(myApp, 'format_responses'):
        raise ValueError('ERROR: myApp.format_responses does not exist for {}'.format(app_id))

    r = myApp.format_responses(responses)

    if type(r) != list and type(r[0]) != dict:
        raise ValueError('ERROR: myApp.format_responses should return a list of dictionaries')

    df = pd.DataFrame(r)
    str_file = StringIO()
    df.to_csv(str_file, encoding='utf-8')
    return str_file
