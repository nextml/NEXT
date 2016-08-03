"""
next_backend Query Resource 
Query resource for handling restful querying of experiments in next_backend. 
"""

from flask.ext.restful import Resource, reqparse

import json
import next.utils
import next.broker.broker
from next.api.api_util import *
import next.utils as utils
from next.api.resource_manager import ResourceManager
from jinja2 import Environment, FileSystemLoader
resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()

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
        post_parser.add_argument('exp_uid', type=str, required=True)
        post_parser.add_argument('args', type=dict, required=False)
        # Validate args with post_parser
        args_data = post_parser.parse_args()
        # Pull app_id and exp_uid from parsed args
        exp_uid = args_data['exp_uid']
        # Fetch app_id data from resource manager
        app_id = resource_manager.get_app_id(exp_uid)
        # Standardized participant_uid
        if 'participant_uid' in args_data['args'].keys():
            args_data['args']['participant_uid'] = exp_uid+"_"+args_data['args']['participant_uid']

        render_widget = args_data['args'].get('widget',False)

        # Execute getQuery 
        response_json,didSucceed,message = broker.applyAsync(app_id,exp_uid,"getQuery", json.dumps(args_data))
        response_dict = json.loads(response_json)
        if not didSucceed:
            return attach_meta({},meta_error['QueryGenerationError'], backend_error=message)

        if render_widget:
            TEMPLATES_DIRECTORY = 'apps/{}/widgets'.format(resource_manager.get_app_id(exp_uid))
            env = Environment(loader=FileSystemLoader(TEMPLATES_DIRECTORY))
            template=env.get_template("getQuery_widget.html")
            return {'html':template.render(query=response_dict), 'args':response_dict}, 200, {'Access-Control-Allow-Origin':'*', 'Content-Type':'application/json'}
        
        return attach_meta(response_dict,meta_success), 200
        
            

