from flask import Blueprint, render_template
from flask_restful import Api, Resource, reqparse, request

from next.utils import utils
from next.lib.pijemont import doc as doc_gen
from next.lib.pijemont import verifier
import next.assistant.target_unpacker as target_unpacker

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
    def post(self):
        args = request.get_json(force=True)
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
