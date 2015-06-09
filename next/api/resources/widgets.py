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
from next.api.keychain import KeyChain
from next.api.widgets_library import widgetManager
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
keychain = KeyChain()
widget_manager = widgetManager()

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
        print "args for this widget request", args
        app_id = resource_manager.get_app_id(args["exp_uid"])
        args["app_id"] = app_id

        # Comment this back in, having some issues with it right now.
        #if not keychain.verify_widget_key(args['exp_uid'], args['widget_key']):
        #    return api_util.attach_meta({}, verification_error), 401
        
        widget = widget_manager.get_widget(args)
        
        return widget, 200, {'Access-Control-Allow-Origin':'*', 'Content-Type':'application/json'}


class WidgetKeys(Resource):

    def post(self):
        """
        Returns a list of widget keys with a given number of tries and duration.

        Inputs: ::\n
                 {
                exp_uid: experiment uid,
                exp_key: experiment key,
                n: number of desired keys,
                tries: numer of tries,
                duration: duration in minutes
             }
        Output: ::\n
            Response: 200, ContentType "text/html"
            { key: perm key }

        """
        args = request.json
        # Not sure verification should even be done at this level, or through the api!!!
        # -as is, verification is being done twice, here and in the keychain - I think it is best to just check in keychain
        if not keychain.verify_exp_key(args['exp_uid'],args['exp_key']):
            return api_util.attach_meta({}, api_util.verification_error)
        
        temp_keys = keychain.create_temp_keys(args['exp_uid'], args['exp_key'], n=args['n'], tries=args.get('tries', 100), duration=args.get('duration', 60) )
        return {'keys':temp_keys}, 200, {'Access-Control-Allow-Origin':'*'}
