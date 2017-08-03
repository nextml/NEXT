import sys
import random
import traceback
import base64
import yaml
from flask import Blueprint, render_template
from flask_restful import Api, Resource, reqparse, request

import next.utils as utils
from next.lib.pijemont import doc as doc_gen
from next.lib.pijemont import verifier
from next.broker.broker import JobBroker
import next.assistant.target_unpacker as target_unpacker
import sys
import json

assistant = Blueprint('assistant',
                      __name__,
                      template_folder='../lib/pijemont/templates',
                      static_folder='../lib/pijemont/static')
assistant_api = Api(assistant)
broker = JobBroker()

@assistant.route('/init/<string:app_id>/form')
def init_form(app_id=None):
    if app_id:
        filename = '{0}/{0}.yaml'.format(app_id)

        api,_ = verifier.load_doc(filename, 'apps/')
        return render_template('form.html',api_doc=api, submit="/api/experiment", function_name="initExp", base_dir="/assistant/static")
    
    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)

@assistant.route('/init')
def init_file(app_id=None):
    return render_template('file.html', target="/assistant/init/experiment", base_dir="/assistant/static")
    
class ExperimentAssistant(Resource):
    def deserialise(self, data):
        start = data.find('\n')
        s = data[:start].decode('ascii')
        # print('s',s)
        d = [x.split(':') for x in s.split(';')]
        # print('d',d)
        start += 1
        ans = {}
        for arg,size in d:
            size = int(size)
            # print('a,s',arg,size)
            ans[arg] = data[start:start+size]
            start += size
        return ans

    def post(self):
        utils.debug_print('POSTED!')
        utils.debug_print('H',request.headers)
        try:
            utils.debug_print('L',len(request.get_data()))
        except Exception as exc:
            print(exc)
            print('OH NO an error in assistant_blueprint!',exc,sys.exc_info())

        # TODO? replace with msgpack
        args = self.deserialise(request.get_data())

        # Unpacking the YAML/ZIP file
        for key in args:
            if key not in {'bucket_id', 'key_id', 'secret_key'}:
                comma_idx = args[key].find(',')
                args[key] = args[key][comma_idx + 1:]
                if args[key] in {'True', 'False'}:
                    args[key] = True if args[key] == 'True' else False
                else:
                    args[key] = base64.decodestring(args[key])

        if all([key not in args for key in ['bucket_id', 'key_id', 'sercret_key']]):
            args['upload'] = False
        else:
            args['upload'] = True

        utils.debug_print('args.keys() = ', args.keys())

        args['args'] = yaml.load(args['args'])

        try:
            init_exp_args = args['args']
            if 'targets' in args.keys():
                target_zipfile = args['targets']
                if args.get('upload', True):
                    bucket_id = args['bucket_id']
                    key_id = args['key_id']
                    secret_key = args['secret_key']

                    targets = target_unpacker.unpack(target_zipfile, key_id,
                                                     secret_key, bucket_id)
                else:
                    filenames = target_unpacker.get_filenames_from_zip(target_zipfile)
                    filenames = [f for f in filenames if f[0] not in {'_', '.'}]
                    if len(filenames) != 1:
                        raise ValueError('Specify exactly one file in the ZIP file')
                    filename = filenames[0]
                    extension = filename.split('.')[-1]
                    targets = target_unpacker.unpack_text_file(target_zipfile,
                                                               kind=extension)
                init_exp_args['args']['targets'] = {'targetset':  targets}

            # Init the experiment:
            app_id = init_exp_args['app_id']
            exp_uid = '%030x' % random.randrange(16**30)

            r = broker.applyAsync(app_id, exp_uid, 'initExp',
                                  json.dumps(init_exp_args))
            response_json, didSucceed, message = r
            if not didSucceed:
                raise ValueError(message)
        except:
            tb = traceback.format_exc()
            info = sys.exc_info()
            if hasattr(info[1], 'message') and len(info[1].message) > 0:
                message = info[1].message
                if 'time' in message:
                    message += ("\nNOTE: error has to do with time; try "
                                "restarting docker, more detail at "
                                "https://stackoverflow.com/questions/27674968/amazon-s3-docker-403-forbidden-the-difference-between-the-request-time-and")
            else:
                message = str(info[1]) + str(info[-1])
                message = '\n'.join(tb.split('\n')[-5:])
            message = message + '\n\nDetails:\n' + tb

            return {'success': False, 'message': message, 'exp_uid': None}

        return {'success': didSucceed, 'message': message, 'exp_uid': exp_uid,
                'app_id': args['args']['app_id']}

assistant_api.add_resource(ExperimentAssistant,'/init/experiment')

@assistant.route('/doc/<string:app_id>/<string:form>')
def docs(app_id=None,form="raw"):
    if app_id:
        filename = '{0}/myApp.yaml'.format(app_id)

        utils.debug_print(filename)
        api,blank,pretty = doc_gen.get_docs(filename,'apps/')
        
        if form == "pretty":
            return render_template('doc.html',doc_string=pretty, base_dir="/assistant/static")
        elif form == "blank":
            return render_template('raw.html',doc=blank)
        elif form == "raw":
            return render_template('raw.html',doc=api)

    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)
