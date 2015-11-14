"""
next dashboard.py
author: Lalit Jain, lalitkumarj@gmail.com
last updated: 9/16/15

Flask controller for dashboards. 
"""
from flask import Blueprint, render_template, url_for
from jinja2 import Environment, PackageLoader, ChoiceLoader

import next.constants as constants
import next.utils as utils
import next.database_client.PermStore as PermStore
from next.api.resource_manager import ResourceManager


# Declare this as the dashboard blueprint
dashboard = Blueprint('dashboard',
                      __name__,
                      template_folder='templates',
                      static_folder='static')
rm = ResourceManager()
db = PermStore.PermStore()

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
            docs,didSucceed,message = db.getDocsByPattern('next_frontend_base',
                                                          'keys',
                                                          {'object_id':exp_uid,
                                                           'type':'exp'})            
            try:
                exp_key = docs[0]['_id']
                experiments.append({'exp_uid': exp_uid, 
                                    'app_id': app_id, 
                                    'start_date': start_date, 
                                    'exp_key': exp_key})
            except IndexError:
                pass

    return render_template('experiment_list.html', 
                           experiments = reversed(experiments))

@dashboard.route('/system_monitor')
def system_monitor():
    """
    Endpoint that renders a page with a simple list of all monitoring. 
    """
    rabbit_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                       15672)
    cadvisor_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                         8888)
    mongodb_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                        28017)
    return render_template('system_monitor.html', 
                           rabbit_url=rabbit_url, 
                           cadvisor_url=cadvisor_url, 
                           mongodb_url=mongodb_url)

@dashboard.route('/experiment_dashboard/<exp_uid>/<app_id>/<exp_key>')
def experiment_dashboard(exp_uid, app_id, exp_key):
    """
    Endpoint that renders the experiment dashboard.

    Inputs: ::\n
    	(string) exp_uid, exp_uid for a current experiment.
    """
    # Not a particularly good way to do this. 
    alg_label_list = rm.get_algs_for_exp_uid(exp_uid)

    exp_start_data = rm.get_app_exp_uid_start_date(exp_uid)+' UTC'
    participant_uids = rm.get_participant_uids(exp_uid)
    num_participants = len(participant_uids)
    num_queries = 0
    for participant_uid in participant_uids:
      queries = rm.get_participant_data(participant_uid, exp_uid)
      num_queries += len(queries)

    # Migrate this code to use keychain
    docs,didSucceed,message = db.getDocsByPattern('next_frontend_base',
                                                  'keys',
                                                  {'object_id': exp_uid,
                                                   'type': 'perm'})
    perm_key = docs[0]['_id']
    alg_list = [{'alg_label':alg['alg_label'],
                 'alg_label_clean':'_'.join(alg['alg_label'].split())}
                for alg in alg_label_list]

    if (constants.NEXT_BACKEND_GLOBAL_HOST and
        constants.NEXT_BACKEND_GLOBAL_PORT):        
        host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                         constants.NEXT_BACKEND_GLOBAL_PORT)
    else:
        host_url = ''
    print 'host_url', host_url
    print constants.NEXT_BACKEND_GLOBAL_HOST, constants.NEXT_BACKEND_GLOBAL_PORT 
    env = Environment(loader=ChoiceLoader([PackageLoader('next.apps.{}'.format(app_id),
                                                         'dashboard'),
                                           PackageLoader('next.dashboard',
                                                         'templates')]))
    try:
      template = env.get_template('{}.html'.format(app_id)) 
    except:
      template = env.get_template('basic.html') 
    return template.render(app_id=app_id,
                           exp_uid=exp_uid,
                           exp_key=exp_key,
                           alg_list=alg_list,
                           host_url=host_url,
                           perm_key=perm_key,
                           url_for=url_for,
                           exp_start_data=exp_start_data,
                           num_participants=num_participants,
                           num_queries=num_queries,
                           )






