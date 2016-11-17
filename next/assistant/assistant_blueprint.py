import base64
import yaml
from flask import Blueprint, render_template
from flask_restful import Api, Resource, reqparse, request

from next.utils import utils
from next.lib.pijemont import doc as doc_gen
from next.lib.pijemont import verifier
import next.assistant.target_unpacker as target_unpacker
import sys

assistant = Blueprint('assistant',
                      __name__,
                      template_folder='../lib/pijemont/templates',
                      static_folder='../lib/pijemont/static')
assistant_api = Api(assistant)

@assistant.route('/init/<string:app_id>/form')
def init_form(app_id=None):
    if app_id:
        filename = '{0}/{0}.yaml'.format(app_id)

        api,_ = verifier.load_doc(filename, 'apps/')
        return render_template('form.html',api_doc=api, submit="/api/experiment", function_name="initExp", base_dir="/assistant/static")
    
    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)

@assistant.route('/init/<string:app_id>/file')
def init_file(app_id=None):
    if app_id:
        return render_template('file.html', target="/assistant/init/experiment", base_dir="/assistant/static")
    
    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)

class ExperimentAssistant(Resource):
    def deserialise(self, data):
        start = data.find('\n')
        s = data[:start].decode('ascii')
        print('s',s)
        d = [x.split(':') for x in s.split(';')]
        print('d',d)
        start += 1
        ans = {}
        for arg,size in d:
            size = int(size)
            print('a,s',arg,size)
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

        for key in args:
            args[key] = base64.decodestring(args[key])

        args['args'] = yaml.load(args['args'])

        utils.debug_print(args['args'])
        bucket_id = args['bucket_id']
        init_exp_args = args['args']
        target_zipfile = args['targets']

        # Unpack the targets
        targets = target_unpacker.unpack(target_zipfile, bucket_id)

        # Init the experiment:
        app_id = args_data['app_id']
        exp_uid = '%030x' % random.randrange(16**30)
        init_exp_args['targets'] = targets
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'initExp',
                                                             json.dumps(init_exp_args))

        return render_template('success.html', exp_uid=exp_uid, app_id=app_id)

assistant_api.add_resource(ExperimentAssistant,'/init/experiment')

@assistant.route('/doc/<string:app_id>/<string:form>')
def docs(app_id=None,form="raw"):
    if app_id:
        filename = '{0}/{0}.yaml'.format(app_id)

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
