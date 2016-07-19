from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask.ext.restful import abort, Api, Resource
from next.api import api_util
from next.utils import utils
from next.api.resources.pijemont import doc as doc_gen
from next.api.resources.pijemont import verifier
import json

# Initialize flask.Flask application and restful.api objects
api = Blueprint('api',
                __name__,
                template_folder='templates',
                static_folder='static')
api_interface = api_util.NextBackendApi(api)

# Format: Resource Class, get url, post url (when applicable)
from next.api.resources.experiment import Experiment
api_interface.add_resource(Experiment,
                           '/experiment',
                           '/experiment/<string:exp_uid>')

# TODO: delete the API endpoints for
from next.api.app_handler import AppHandler
api_interface.add_resource(AppHandler,
                           '/experiment/<string:exp_uid>/custom/function_name',
                           '/experiment/custom/<string:function_name>')

from next.api.resources.get_query import getQuery
api_interface.add_resource(getQuery,
                           '/experiment/<string:exp_uid>/getQuery',
                           '/experiment/getQuery')

from next.api.resources.process_answer import processAnswer
api_interface.add_resource(processAnswer, '/experiment/processAnswer')
from next.api.resources.about import About
api_interface.add_resource(About, '/about', '/about/<string:app_id>')

from next.api.resources.logs import Logs
api_interface.add_resource(Logs,
                           '/experiment/<string:exp_uid>/logs',
                           '/experiment/<string:exp_uid>/logs/<log_type>')

from next.api.resources.participants import Participants
api_interface.add_resource(Participants,
                           '/experiment/<string:exp_uid>/participants')

from next.api.resources.database import DatabaseBackup, DatabaseRestore
api_interface.add_resource(DatabaseBackup,'/database/databasebackup')
api_interface.add_resource(DatabaseRestore,'/database/databaserestore')


@api.route('/init/<string:app_id>')
def init_form(app_id=None):
    if app_id:
        apps_path = 'next/apps/Apps/'
        filename = apps_path + '{0}/{0}.yaml'.format(app_id)

        api,_ = verifier.load_doc(filename,'next/apps/')
        return render_template('next.html',api_doc=api)
    
    message = ('Welcome to the next.discovery system.\n '
               'Available apps {}'.format(', '.join(utils.get_supported_apps())))

    return api_util.attach_meta({}, meta_success, message=message)

@api.route('/doc/<string:app_id>/<string:form>')
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

    return api_util.attach_meta({}, meta_success, message=message)
