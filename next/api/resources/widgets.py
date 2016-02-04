"""
next_backend Widget Resource 
author: Christopher Fernandez, Lalit Jain
"""
from flask import Flask, request
from flask.ext import restful
from flask.ext.restful import Resource, reqparse

import json
import next.utils
import next.broker.broker
from next.api.api_util import *
from next.api.api_util import APIArgument

from next.api.targetmapper import TargetMapper

from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()

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

class Widgets(Resource):
#    def options(self):
#        return 'OK', 200, {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'}

    def post(self):
        """
        Returns a specified widget.

        Inputs: ::\n
                 {
                name: widget name,
                exp_id: experiment id,
                widget_key: widget key 
                    args: application and widget dependent args, can normally be ignored
              }
        Output: ::\n
            Response: widget_html, 200, ContentType "text/html", 

        """
        args = request.get_json()
        app_id = str(resource_manager.get_app_id(args["exp_uid"]))
        args['app_id'] = str(app_id)

        # Comment this back in, having some issues with it right now.
        app_module = __import__('next.apps.{}.widgets'.format(app_id),
                                fromlist=[app_id])
        app_class = getattr(app_module, 'WidgetGenerator')
        app = app_class()
        widget_func = getattr(app, args['name'])
        widget = widget_func(args)
        
        return widget, 200, {'Access-Control-Allow-Origin':'*', 'Content-Type':'application/json'}
