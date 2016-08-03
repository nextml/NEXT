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
import next.utils as utils


# Declare this as the dashboard blueprint
dashboard = Blueprint('dashboard',
                      __name__,
                      template_folder='templates',
                      static_folder='static')
rm = ResourceManager()
db = PermStore.PermStore()

broker = next.broker.broker.JobBroker()

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
    return render_template('experiment_list.html',
                           experiments = reversed(experiments))

@dashboard.route('/get_stats', methods=['POST'])
def get_stats():
    args_dict = request.json
    exp_uid = args_dict['exp_uid']
    app_id = rm.get_app_id(exp_uid)
    
    response_json,didSucceed,message = broker.dashboardAsync(app_id,
                                                             exp_uid,
                                                             args_dict)
    response_dict = json.loads(response_json,parse_float=lambda o:round(float(o),4))
    response_json = json.dumps(response_dict)
    
    return response_json
    #with open(os.path.join('next/apps', 'Apps/{}/{}.yaml'.format(app_id, app_id)),'r') as f:
    #    reference_dict = yaml.load(f)        
    # verification
    #args_dict = Verifier.verify(args_dict, reference_dict['getStats']['values'])
    #stat_id = args_dict['args'].pop('stat_id',None)
    # myApp
    #app = utils.get_app(app_id, exp_uid, dba, ell) #__import__('apps.'+app_id, fromlist=[''])
    #butler = Butler.Butler(app_id, exp_uid, app.myApp.TargetManager, dba, ell)

    # dashboard
    #dashboard_string = 'apps.' + app_id + \
    #                   '.dashboard.Dashboard'
    #dashboard_module = __import__(dashboard_string, fromlist=[''])
    #dashboard = getattr(dashboard_module, app_id+'Dashboard')
    #dashboard = dashboard(butler.db, butler.ell)
    #stats_method = getattr(dashboard, stat_id)
    #return jsonify(stats_method(app_id, exp_uid, butler, **args_dict['args']['params']))


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

@dashboard.route('/experiment_dashboard/<exp_uid>/<app_id>')
def experiment_dashboard(exp_uid, app_id):
    """
    Endpoint that renders the experiment dashboard.

    Inputs: ::\n
    	(string) exp_uid, exp_uid for a current experiment.
    """
    simple_flag = int(request.args.get('simple',0))

    if simple_flag<2:
        git_hash = rm.get_git_hash_for_exp_uid(exp_uid)
        exp_start_data = rm.get_app_exp_uid_start_date(exp_uid)+' UTC'
        participant_uids = rm.get_participant_uids(exp_uid)
        num_participants = len(participant_uids)
        num_queries = 0
        for participant_uid in participant_uids:
            queries = rm.get_participant_data(participant_uid, exp_uid)
            num_queries += len(queries)
    else:
        git_hash = ''
        exp_start_data = ''
        num_participants = -1
        num_queries = -1

    # Not a particularly good way to do this.
    alg_label_list = rm.get_algs_for_exp_uid(exp_uid)
    alg_list = [{'alg_label':alg['alg_label'],
                 'alg_label_clean':'_'.join(alg['alg_label'].split())}
                for alg in alg_label_list]

    if (constants.NEXT_BACKEND_GLOBAL_HOST and
        constants.NEXT_BACKEND_GLOBAL_PORT):
        host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                         constants.NEXT_BACKEND_GLOBAL_PORT)
    else:
        host_url = ''
    env = Environment(loader=ChoiceLoader([PackageLoader('apps.{}'.format(app_id),
                                                         'dashboard'),
                                           PackageLoader('next.dashboard',
                                                         'templates')]))
    template = env.get_template('{}.html'.format(app_id)) # looks for /next/apps/{{ app_id }}/dashboard/{{ app_id }}.html

    return template.render(app_id=app_id,
                           exp_uid=exp_uid,
                           git_hash=git_hash,
                           alg_list=alg_list,
                           host_url=host_url,
                           exceptions_present=exceptions_present(exp_uid, host_url),
                           url_for=url_for,
                           exp_start_data=exp_start_data,
                           num_participants=num_participants,
                           num_queries=num_queries,
                           simple_flag=int(simple_flag))


def exceptions_present(exp_uid, host_url):
    import yaml
    url = '{}/api/experiment/{}/logs/APP-EXCEPTION'.format(host_url, exp_uid)
    r = requests.get(url)
    logs = yaml.load(r.content)['log_data']
    return True if len(logs) > 0 else False

