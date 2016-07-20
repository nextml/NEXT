from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask.ext.restful import abort, Api, Resource
from next.api import api_util
from next.utils import utils
from next.assistant.pijemont import doc as doc_gen
from next.assistant.pijemont import verifier
import json

assistant = Blueprint('assistant',
                      __name__,
                      template_folder='templates',
                      static_folder='static')

@assistant.route('/init/<string:app_id>')
def init_form(app_id=None):
    if app_id:
        apps_path = 'next/apps/Apps/'
        filename = apps_path + '{0}/{0}.yaml'.format(app_id)

        api,_ = verifier.load_doc(filename,'next/apps/')
        return render_template('next.html',api_doc=api)
    
    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)

@assistant.route('/doc/<string:app_id>/<string:form>')
def docs(app_id=None,form="raw"):
    if app_id:
        apps_path = 'next/apps/Apps/'
        filename = apps_path + '{0}/{0}.yaml'.format(app_id)

        utils.debug_print(filename)
        api,blank,pretty = doc_gen.get_docs(filename,'next/apps/')
        
        if form == "pretty":
            return render_template('doc.html',doc_string=pretty)
        elif form == "blank":
            return render_template('raw.html',doc=blank)
        elif form == "raw":
            return render_template('raw.html',doc=api)

    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return render_template('raw.html',doc=message)
