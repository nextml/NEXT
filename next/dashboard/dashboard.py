"""
next dashboard.py
author: Lalit Jain, lalitkumarj@gmail.com
last updated: 9/16/15

Flask controller for dashboards.
"""
import os
import json
import yaml
from flask import Blueprint, render_template, url_for, request, jsonify
from jinja2 import Environment, PackageLoader, ChoiceLoader
import requests

import next.broker.broker 
import next.constants as constants
import next.database_client.PermStore as PermStore
from next.api.resource_manager import ResourceManager
import next.api.api_util as api_util

# Declare this as the dashboard blueprint
dashboard = Blueprint('dashboard',
                      __name__,
                      template_folder='templates',
                      static_folder='static')

rm = ResourceManager()
db = PermStore.PermStore()
broker = next.broker.broker.JobBroker()

import next.apps.Butler as Butler
Butler = Butler.Butler

# add database commands
dashboard_interface = api_util.NextBackendApi(dashboard)
from next.dashboard.database import DatabaseBackup, DatabaseRestore
dashboard_interface.add_resource(DatabaseBackup,'/database/databasebackup', endpoint='databasebackup')
dashboard_interface.add_resource(DatabaseRestore,'/database/databaserestore', endpoint='databaserestore')


@dashboard.route('/experiment_list')
def experiment_list():
    """
    Endpoint that renders a page with a simple list of all experiments.
    """
    # Experiments set
    experiments = []
    for app_id in rm.get_app_ids():
        for exp_uid in rm.get_app_exp_uids(app_id):
            start_date = rm.get_app_exp_uid_start_date(exp_uid)
            try:
                experiments.append({'exp_uid': exp_uid,
                                    'app_id': app_id,
                                    'start_date': start_date,
                                    'num_participants':len(rm.get_participant_uids(exp_uid)),
                                    })
            except IndexError as e:
                print e
                pass

    host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                     constants.NEXT_BACKEND_GLOBAL_PORT)
    if constants.SITE_KEY:
        dashboard_url='{}/dashboard/{}'.format(host_url, constants.SITE_KEY)
    else:
        dashboard_url='{}/dashboard'.format(host_url)
        
    return render_template('experiment_list.html',
                           dashboard_url=dashboard_url,
                           experiments = reversed(experiments))

@dashboard.route('/get_stats', methods=['POST'])
def get_stats():
    args_dict = request.json
    exp_uid = args_dict['exp_uid']
    app_id = rm.get_app_id(exp_uid)
    
    response_json,didSucceed,message = broker.dashboardAsync(app_id,exp_uid,args_dict)
    response_dict = json.loads(response_json,parse_float=lambda o:round(float(o),4))
    response_json = json.dumps(response_dict)
    return response_json


@dashboard.route('/system_monitor')
def system_monitor():
    """
    Endpoint that renders a page with a simple list of all monitoring.
    """
    host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                     constants.NEXT_BACKEND_GLOBAL_PORT)
    if constants.SITE_KEY:
        dashboard_url='{}/dashboard/{}'.format(host_url, constants.SITE_KEY)
    else:
        dashboard_url='{}/dashboard'.format(host_url)

    rabbit_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                       15672)
    cadvisor_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                         8888)
    mongodb_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                        28017)
    return render_template('system_monitor.html',
                           dashboard_url=dashboard_url,
                           rabbit_url=rabbit_url,
                           cadvisor_url=cadvisor_url,
                           mongodb_url=mongodb_url)


@dashboard.route('/experiment_dashboard/<exp_uid>/<app_id>')
def experiment_dashboard(exp_uid, app_id):
    """
    Endpoint that renders the experiment dashboard.

    Inputs: ::\n
    	(string) exp_uid, exp_uid for a current experiment.
    """
    simple_flag = int(request.args.get('simple',0))
    force_recompute = int(request.args.get('force_recompute',1))

    # Not a particularly good way to do this.
    alg_label_list = rm.get_algs_for_exp_uid(exp_uid)
    alg_list = [{'alg_label':alg['alg_label'],
                 'alg_label_clean':'_'.join(alg['alg_label'].split())}
                for alg in alg_label_list]

    host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                     constants.NEXT_BACKEND_GLOBAL_PORT)
    if constants.SITE_KEY:
        dashboard_url='{}/dashboard/{}'.format(host_url, constants.SITE_KEY)
    else:
        dashboard_url='{}/dashboard'.format(host_url)
        
    env = Environment(loader=ChoiceLoader([PackageLoader('next.apps.Apps.{}'.format(app_id),
                                                         'dashboard'),
                                           PackageLoader('next.dashboard',
                                                         'templates')]))
    template = env.get_template('{}.html'.format(app_id)) # looks for /next/apps/{{ app_id }}/dashboard/{{ app_id }}.html
    return template.render(app_id=app_id,
                           exp_uid=exp_uid,
                           alg_list=alg_list,
                           host_url=host_url,
                           dashboard_url=dashboard_url,
                           exceptions_present=exceptions_present(exp_uid, host_url),
                           url_for=url_for,
                           simple_flag=int(simple_flag),
                           force_recompute=int(force_recompute))


def exceptions_present(exp_uid, host_url):
    url = '{}/api/experiment/{}/logs/APP-EXCEPTION'.format(host_url, exp_uid)
    r = requests.get(url)
    logs = yaml.load(r.content)['log_data']
    return True if len(logs) > 0 else False

