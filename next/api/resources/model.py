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


class GetModel(Resource):
    def get(self, exp_uid, **kwargs):
        """
        args are encoded in the URL as JSON. These args are passed to getModel
        as `args`.

        `csv` is included in `args`. It can be

        e.g.,
        /api/experiment/{exp_uid}/getModel?args={'format':True,'csv':True}

        """
        args = request.args.get('args', '{}')
        args = ast.literal_eval(args)
        format = args.get('format', False)
        csv = args.get('csv', False)
        if 'csv' in args:
            del args['csv']
        if csv not in {'0', 0, False}:
            csv = True
        if csv and 'alg_label' in args:
            raise ValueError('Cannot return one CSV for one algorithm')
        if csv and not format:
            raise ValueError('cannot specify csv=True and args["format"]=False.')

        exp_uid = str(exp_uid)
        args = {'exp_uid': exp_uid, 'args': args}
        app_id = resource_manager.get_app_id(exp_uid)

        response_json, _, _ = broker.applyAsync(app_id, exp_uid, "getModel",
                                                json.dumps(args))
        response_dict = json.loads(response_json)

        formatted_responses = 'models' in response_dict.keys()
        if csv and formatted_responses:
            csvs = [{'data': _result_to_csv_str(results),
                     'filename': alg_label + '.csv'}
                    for alg_label, results in response_dict['models'].items()]
            zipfile = _create_zipfile(csvs)
            return send_file(zipfile,
                             attachment_filename='results.zip',
                             as_attachment=True)

        return attach_meta(response_dict, meta_success), 200


def _get_target_mapping(exp_uid, bucket_id='targets'):
    from next.apps.SimpleTargetManager import SimpleTargetManager
    meta = ('Mapping from indices totarget filenames, which all '
            'algorithmis use internally')
    target_manager = SimpleTargetManager(db)
    targets = target_manager.get_targetset(exp_uid)
    mapping = {target['target_id']: target for target in targets}
    return {'meta': meta, 'mapping': mapping}


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
