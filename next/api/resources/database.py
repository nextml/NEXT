"""
next_backend Logs Resource 
author: Christopher Fernandez, Lalit Jain
Logs resource for all logs associated with a specified experiment. 
"""

'''
example use:
get a tripletMDS query:
curl -X GET http://localhost:8001/api/experiment/[exp_uid]/[exp_key]/logs
'''
import json
import time

from flask import Flask, Response
from flask.ext import restful
from flask.ext.restful import Resource, reqparse

import next.utils
import next.broker.broker
from next.api.api_util import *
from next.api.api_util import APIArgument
from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager
from next.database.database_lib import *

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
keychain = KeyChain()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed. 
post_parser = reqparse.RequestParser(argument_class=APIArgument)
meta_success = {
    'code': 200,
    'status': 'OK'
}

# Logs resource class
class DatabaseBackup(Resource):
    def get(self):
        """
        .. http:get:: /databaseBackup

        Get a tar copy of the database.

        **Example request**:

        .. sourcecode:: http

        GET /databaseBackup HTTP/1.1
        
        **Example response**:

        .. sourcecode:: http
        
        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        :statuscode 200: Database backup successfully returned
        :statuscode 400: database backup failed to be generated
    	""" 
        name = str(time.gmtime())
        location = make_mongodump(name)
        
        f = file(location)
        return Response(f, 200)

