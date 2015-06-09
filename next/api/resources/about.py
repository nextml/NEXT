"""
next_backend About response
author: Christopher Fernandez, Lalit Jain
About request. Good place to put version information.
"""

from flask import Flask
from flask.ext import restful
from flask.ext.restful import Resource, reqparse
from next.api.api_util import *

meta_success = {'status':'OK', 'code':200}

class About(Resource):
    def get(self):
        """
        .. http:get:: /about

        Return an about message. 

        **Example request**:

        .. sourcecode:: http

        GET /about HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu
        
        **Example response**:

        .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        [
        	message: "Welcome to the next.discovery system."
        	status: {
        		code: 200,
        		status: OK,
       		},
        	
        ]

        :statuscode 200: no error
        """
        return attach_meta({},meta_success,message= "Welcome to the next.discovery system.")

    def post(self):
        """
        .. http:pose:: /about

        Return an about message. 

        **Example request**:

        .. sourcecode:: http

        POST /about HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu
        
        **Example response**:

        .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        [
        	message: "Welcome to the next.discovery system."
        	status: {
        		code: 200,
        		status: OK,
       		},
        	
        ]

        :statuscode 200: no error
        """
        return attach_meta({},meta_success,message= "Welcome to the next.discovery system.")

    

