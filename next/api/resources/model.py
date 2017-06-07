from StringIO import StringIO
import pandas as pd
from flask import Flask, send_file, request, abort
from flask_restful import Resource, reqparse
import traceback
import time
from next.api.api_util import attach_meta
import pandas

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
    def get(self, exp_uid, csv=False):
        model_args = post_parser.parse_args()
        csv = request.args.get('csv', False)
        if int(csv) != 0:
            csv = True

        utils.debug_print(model_args, request.args, csv)
        args = {'exp_uid': exp_uid, 'args': model_args}

        algs = resource_manager.get_algs_for_exp_uid(exp_uid)
        app_id = resource_manager.get_app_id(exp_uid)

        results = {}
        for alg in algs:
            args['args']['alg_label'] = alg['alg_label']

            r = broker.applyAsync(app_id,exp_uid,"getModel", json.dumps(args))
            response_json, didSucceed, message = r

            response_dict = json.loads(response_json)
            response_dict['alg'] = alg
            results[alg['alg_label']] = response_dict

        results['target_mapping'] = _get_target_mapping(exp_uid)

        if csv:
            if 'target' not in response_dict:
                return ('`target` not a key for getModel results. Likely means that '
                        'application does not provide ranking/sorting of '
                        'objects that can be formulated as table. Download '
                        'the JSON object and use the included `target_id` '
                        'mapping to index the alg results')

            csvs = [{'data': format_results(results['targets']),
                     'filename': alg_label + '.csv'}
                    for alg_label, results in results.items()]
            zipfile = _create_zipfile(csvs)
            return send_file(zipfile,
                             attachment_filename='alg_results.zip',
                             as_attachment=True)

        return attach_meta(results, meta_success), 200


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


def format_results(results):
    formatted_results = [{k: v for k, v in result.items() if k != 'target'}
                         for result in results]

    for result, formatted_result in zip(results, formatted_results):
        for key in result['target'].keys():
            if not ('alt' in key):
                formatted_result[key] = result['target'][key]
        for key in ['_id', 'index']:
            if key in formatted_result:
                del formatted_result[key]

    df = pd.DataFrame(formatted_results)
    str_file = StringIO()
    df.to_csv(str_file, encoding='utf-8')
    return str_file.getvalue()  # return a str object
