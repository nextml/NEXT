from flask.ext.restful import Resource, reqparse

import json
import next.utils
import next.broker.broker
import next.api.api_util as api_util
from next.api.api_util import *
from next.api.api_util import APIArgument

from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
keychain = KeyChain()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed.
post_parser = reqparse.RequestParser(argument_class=APIArgument)

# Custom errors for GET and POST verbs on experiment resource
meta_error = {
    'Error': {
        'message': "There was an error calling this API endpoint ",
        'code': 400,
        'status':'FAIL'
    }
}

meta_success = {
    'code': 200,
    'status': 'OK'
}



class AppHandler(Resource):
    def post(self, exp_uid, exp_key, function_name):
        try:
            post_parser.add_argument('exp_uid', type=str, required=True, help="Experiment ID Required.")
            post_parser.add_argument('exp_key', type=str, required=True, help="Experiment key Required.")
            post_parser.add_argument('args', type=dict, required=False, help="Experiment args Required.")


            # Validate args with post_parser
            args_data = post_parser.parse_args()

            # Pull app_id and exp_uid from parsed args
            exp_uid = args_data["exp_uid"]
            exp_key = args_data["exp_key"]
            if not keychain.verify_exp_key(exp_uid, exp_key):
                return api_util.attach_meta({}, api_util.verification_error), 401

            # Fetch app_id data from resource manager
            app_id = resource_manager.get_app_id(exp_uid)

            args_json = json.dumps(args_data["args"])

            # This allows different apps to define custom functions,
            # and hit the API with those functions.
            # TODO: test this feature
            # implemented by Scott Sievert, 2016-1-26
            response_json, didSucceed, message = broker.applyAsync(app_id, exp_uid, function_name, args_json)

            if not didSucceed:
                raise Exception(message)

            response_dict = json.loads(response_json)
            return attach_meta(response_dict, meta_success), 200

        except Exception, error:
            return attach_meta({}, meta_error['Error'], backend_error=message)
