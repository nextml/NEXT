from StringIO import StringIO
import pandas as pd
from flask import Flask, send_file, request, abort
from flask_restful import Resource, reqparse
import traceback
import time
from next.api.api_util import attach_meta
import pandas
import ast

import json
from io import BytesIO
import zipfile

import next.utils
import next.utils as utils
import next.api.api_util as api_util
from next.api.api_util import APIArgument
from next.api.resource_manager import ResourceManager
from next.database_client.DatabaseAPI import DatabaseAPI
from next.logging_client.LoggerAPI import LoggerAPI
db = DatabaseAPI()
ell = LoggerAPI()
broker = next.broker.broker.JobBroker()
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


class GetResults(Resource):
    def get(self, exp_uid, **kwargs):
        """
        Endpoint:
        /api/experiment/{exp_uid}/getResults?csv=1
        """
        csv = request.args.get('csv', False)
        if type(csv) in {unicode, str}:
            csv = str(csv).lower()
        csv = csv not in {'0', 0, False, 'false'}

        exp_uid = str(exp_uid)
        args = {'exp_uid': exp_uid, 'args': {}}
        app_id = resource_manager.get_app_id(exp_uid)

        response_json, _, _ = broker.applyAsync(app_id, exp_uid, "getResults", '{}')
        results = json.loads(response_json)
        response = {'results': results}

        if csv:
            csvs = [{'data': _result_to_csv_str(result),
                     'filename': alg_label + '.csv'}
                    for alg_label, result in results.items()]
            zipfile = _create_zipfile(csvs)
            return send_file(zipfile,
                             attachment_filename='results.zip',
                             as_attachment=True)

        return attach_meta(response, meta_success), 200


def _create_zipfile(files):
    """ adapted from https://stackoverflow.com/questions/27337013/how-to-send-zip-files-in-the-python-flask-framework/27337047#27337047 """
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for indiv_file in files:
            data = zipfile.ZipInfo(indiv_file['filename'])
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, indiv_file['data'])
    memory_file.seek(0)
    return memory_file


def _result_to_csv_str(result_list):
    df = pd.DataFrame(result_list)
    str_file = StringIO()
    df.to_csv(str_file, encoding='utf-8')
    return str_file.getvalue()
