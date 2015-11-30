"""
next_backend About response
author: Christopher Fernandez, Lalit Jain
About request. Good place to put version information.
"""

from flask import Flask
from flask.ext import restful
from flask.ext.restful import Resource, reqparse


from next.utils import utils
import next.api.api_util as api_util 

meta_success = {'status':'OK', 'code':200}

class About(Resource):
    def get(self, app_id=None):
        if app_id:
            return api_util.attach_meta(utils.get_app_info_object(app_id),
                                        meta_success), 200
        message = ('Welcome to the next.discovery system.\n '
                   'Available apps {}'.format(', '.join(utils.get_supported_apps())))
        return api_util.attach_meta({},
                                    meta_success,
                                    message=message)
