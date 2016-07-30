from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask.ext.restful import abort, Api, Resource
from next.api import api_util
from next.utils import utils
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
