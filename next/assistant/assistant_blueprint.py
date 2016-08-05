from flask import Blueprint, render_template
from next.utils import utils
from next.lib.pijemont import doc as doc_gen
from next.lib.pijemont import verifier


assistant = Blueprint('assistant',
                      __name__,
                      template_folder='../lib/pijemont/templates',
                      static_folder='../lib/pijemont/static')

@assistant.route('/init/<string:app_id>')
def init_form(app_id=None):
    if app_id:
        filename = 'Apps/{0}/{0}.yaml'.format(app_id)

        api,_ = verifier.load_doc(filename,'next/apps/')
        return render_template('form.html',api_doc=api,submit="/api/experiment", function_name="initExp", base_dir="/assistant/static")
    
    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)

@assistant.route('/doc/<string:app_id>/<string:form>')
def docs(app_id=None,form="raw"):
    if app_id:
        filename = 'Apps/{0}/{0}.yaml'.format(app_id)

        utils.debug_print(filename)
        api,blank,pretty = doc_gen.get_docs(filename,'next/apps/')
        
        if form == "pretty":
            return render_template('doc.html',doc_string=pretty, base_dir="/assistant/static")
        elif form == "blank":
            return render_template('raw.html',doc=blank)
        elif form == "raw":
            return render_template('raw.html',doc=api)

    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)
