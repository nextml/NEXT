import numpy
import numpy as np
import numpy.random
import random
import json
import time
from datetime import datetime
import requests
from scipy.linalg import norm
import time
from multiprocessing import Pool
import os
import sys

HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost') \
           + ':' + os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

def test_api(assert_200=True, num_arms=15, num_clients=25, delta=0.05,
             total_pulls_per_client=15, num_experiments=1):

    app_id = 'DuelingBanditsPureExploration'
    true_means = numpy.array(range(num_arms)[::-1])/float(num_arms)
    pool = Pool(processes=num_clients)
    supported_alg_ids = ['BR_LilUCB', 'BR_Random']

    alg_list = []
    for i, alg_id in enumerate(supported_alg_ids):
        alg_item = {}
        alg_item['alg_id'] = alg_id
        alg_item['alg_label'] = alg_id+'_'+str(i)
        alg_list.append(alg_item)

    params = []
    for algorithm in alg_list:
        params.append({'alg_label': algorithm['alg_label'], 'proportion':1./len(alg_list)})
    algorithm_management_settings = {}
    algorithm_management_settings['mode'] = 'fixed_proportions'
    algorithm_management_settings['params'] = params

    print algorithm_management_settings

    #################################################
    # Test POST Experiment
    #################################################
    initExp_args_dict = {}
    initExp_args_dict['args'] = {'alg_list': alg_list,
                                 'algorithm_management_settings': algorithm_management_settings,
                                 'context': 'Boom baby dueling works',
                                 'context_type': 'text',
                                 'debrief': 'You want a debrief, here is your test debrief',
                                 'failure_probability': 0.05,
                                 'instructions': 'You want instructions, here are your test instructions',
                                 'participant_to_algorithm_management': 'one_to_many',
                                 'targets': {'n': num_arms}}

    initExp_args_dict['app_id'] = app_id
    initExp_args_dict['site_id'] = 'replace this with working site id'
    initExp_args_dict['site_key'] = 'replace this with working site key'

    exp_info = []
    for ell in range(num_experiments):
        url = "http://"+HOSTNAME+"/api/experiment"
        response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
        print "POST initExp response =",response.text, response.status_code
        if assert_200: assert response.status_code is 200
        initExp_response_dict = json.loads(response.text)

        exp_uid = initExp_response_dict['exp_uid']

        exp_info.append({'exp_uid':exp_uid,})

        #################################################
        # Test initExperiment
        #################################################
        url = "http://"+HOSTNAME+"/api/experiment/"+exp_uid
        response = requests.get(url)
        print "GET experiment response =", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        initExp_response_dict = json.loads(response.text)

    ###################################
    # Generate participants
    ###################################
    participants = []
    pool_args = []
    for i in range(num_clients):
        participant_uid = '%030x' % random.randrange(16**30)
        participants.append(participant_uid)

        experiment = numpy.random.choice(exp_info)
        exp_uid = experiment['exp_uid']
        pool_args.append((exp_uid, participant_uid, total_pulls_per_client,
                          true_means,assert_200))

    results = pool.map(simulate_one_client, pool_args)

    for result in results:
        print result

    # Test loading the dashboard
    dashboard_url = ("http://" + HOSTNAME + "/dashboard"
                     "/experiment_dashboard/{}/{}".format(exp_uid, app_id))
    response = requests.get(dashboard_url)
    if assert_200: assert response.status_code is 200

    stats_url = ("http://" + HOSTNAME + "/dashboard"
                 "/get_stats".format(exp_uid, app_id))

    args =  {'exp_uid': exp_uid, 'args': {'params': {'alg_label':
        supported_alg_ids[0]}}}
    args =  {'exp_uid': exp_uid, 'args': {'params': {}}}
    alg_label = alg_list[0]['alg_label']
    params = {'api_activity_histogram': {},
      'compute_duration_multiline_plot': {'task': 'getQuery'},
      'compute_duration_detailed_stacked_area_plot': {'alg_label': alg_label, 'task': 'getQuery'},
      'response_time_histogram': {'alg_label': alg_label},
      'network_delay_histogram': {'alg_label': alg_label}}
    for stat_id in ['api_activity_histogram',
                    'compute_duration_multiline_plot',
                    'compute_duration_detailed_stacked_area_plot',
                    'response_time_histogram',
                    'network_delay_histogram']:
            args['args']['params'] = params[stat_id]
            args['args']['stat_id'] = stat_id
            response = requests.post(stats_url, json=args)
            if assert_200: assert response.status_code is 200


def simulate_one_client(input_args):
    exp_uid,participant_uid,total_pulls,true_means,assert_200 = input_args
    avg_response_time = 1.

    getQuery_times = []
    processAnswer_times = []
    for t in range(total_pulls):
        print "        Participant {} had {} total pulls: ".format(participant_uid, t)

        #######################################
        # test POST getQuery #
        #######################################
        #  getQuery_args_dict = {'args': {'participant_uid': participant_uid},
                              #  'exp_uid': exp_uid}

        # return a widget 1/5 of the time (normally, use HTML)
        widget = random.choice([True] + 4*[False])
        getQuery_args_dict = {'args': {'participant_uid': participant_uid,
                                       'widget': widget},
                              'exp_uid': exp_uid}

        url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
        response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})
        #  print "POST getQuery response = ", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        #  print "POST getQuery duration = ", dt
        getQuery_times.append(dt)

        query_dict = json.loads(response.text)
        if widget:
            query_dict = query_dict['args']
        query_uid = query_dict['query_uid']
        targets = query_dict['target_indices']

        left = targets[0]['target']
        right = targets[1]['target']

        # generate simulated reward #
        #############################
        # sleep for a bit to simulate response time

        ts = time.time()

        time.sleep(avg_response_time*numpy.random.rand())

        #  print left
        reward_left = true_means[left['target_id']] + numpy.random.randn()*0.5
        reward_right = true_means[right['target_id']] + numpy.random.randn()*0.5
        if reward_left > reward_right:
            target_winner = left
        else:
            target_winner = right

        response_time = time.time() - ts


        #############################################
        # test POST processAnswer 
        #############################################
        processAnswer_args_dict = {'args': {'query_uid': query_uid,
                                            'response_time': response_time,
                                            'target_winner': target_winner["target_id"]},
                                   'exp_uid': exp_uid}

        url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
        #  print "POST processAnswer args = ", processAnswer_args_dict
        response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
        #  print "POST processAnswer response", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        #  print "POST processAnswer duration = ", dt
        processAnswer_times.append(dt)
        #  print
        processAnswer_json_response = eval(response.text)

    processAnswer_times.sort()
    getQuery_times.sort()
    return_str = '%s \n\t getQuery\t : %f (5),        %f (50),        %f (95)\n\t processAnswer\t : %f (5),        %f (50),        %f (95)\n' % (participant_uid,getQuery_times[int(.05*total_pulls)],getQuery_times[int(.50*total_pulls)],getQuery_times[int(.95*total_pulls)],processAnswer_times[int(.05*total_pulls)],processAnswer_times[int(.50*total_pulls)],processAnswer_times[int(.95*total_pulls)])
    return return_str


def timeit(f):
    """
    Refer to next.utils.timeit for further documentation
    """
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        if type(result)==tuple:
            return result + ((te-ts),)
        else:
            return result,(te-ts)
    return timed

if __name__ == '__main__':
    print HOSTNAME
    test_api()
    #    test_api(assert_200=True, num_arms=5, num_clients=10, delta=0.05,
                #    total_pulls_per_client=10, num_experiments=1)
