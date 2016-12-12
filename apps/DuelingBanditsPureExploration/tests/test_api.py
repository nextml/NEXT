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
try:
    import next.apps.test_utils as test_utils
except:
    sys.path.append('../../../next/apps')
    import test_utils


def test_validation_params():
    params = [{'num_tries': 5},
              {'query_list': [[0, 1], [1, 2], [3, 4]]}]
    for param in params:
        print(param)
        test_api(params=param)


def test_api(assert_200=True, num_arms=5, num_clients=8, delta=0.05,
             total_pulls_per_client=5, num_experiments=1,
             params={'num_tries': 5}):

    app_id = 'DuelingBanditsPureExploration'
    true_means = numpy.array(range(num_arms)[::-1])/float(num_arms)
    pool = Pool(processes=num_clients)
    supported_alg_ids = ['BR_LilUCB', 'BR_Random', 'ValidationSampling']

    alg_list = []
    for i, alg_id in enumerate(supported_alg_ids):
        alg_item = {}
        if alg_id == 'ValidationSampling':
            alg_item['params'] = params
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
                                 'context': 'Context for Dueling Bandits',
                                 'context_type': 'text',
                                 'debrief': 'Test debried.',
                                 'failure_probability': 0.05,
                                 'instructions': 'Test instructions.',
                                 'participant_to_algorithm_management': 'one_to_many',
                                 'targets': {'n': num_arms}}

    initExp_args_dict['app_id'] = app_id
    initExp_args_dict['site_id'] = 'replace this with working site id'
    initExp_args_dict['site_key'] = 'replace this with working site key'

    exp_info = []
    for ell in range(num_experiments):
        exp_info += [test_utils.initExp(initExp_args_dict)[1]]

    # Generate participants
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
        result

    test_utils.getModel(exp_uid, app_id, supported_alg_ids, alg_list)

def simulate_one_client(input_args):
    exp_uid,participant_uid,total_pulls,true_means,assert_200 = input_args

    getQuery_times = []
    processAnswer_times = []
    for t in range(total_pulls):
        print "        Participant {} had {} total pulls: ".format(participant_uid, t)

        # test POST getQuery #
        # return a widget 1/5 of the time (normally, use HTML)
        widget = random.choice([True] + 4*[False])
        getQuery_args_dict = {'args': {'participant_uid': participant_uid,
                                       'widget': widget},
                              'exp_uid': exp_uid}
        query_dict, dt = test_utils.getQuery(getQuery_args_dict)
        getQuery_times.append(dt)

        if widget:
            query_dict = query_dict['args']
        query_uid = query_dict['query_uid']
        targets = query_dict['target_indices']

        left = targets[0]['target']
        right = targets[1]['target']

        # sleep for a bit to simulate response time
        ts = test_utils.response_delay()

        #  print left
        reward_left = true_means[left['target_id']] + numpy.random.randn()*0.5
        reward_right = true_means[right['target_id']] + numpy.random.randn()*0.5
        if reward_left > reward_right:
            target_winner = left
        else:
            target_winner = right

        response_time = time.time() - ts

        # test POST processAnswer 
        processAnswer_args_dict = {'args': {'query_uid': query_uid,
                                            'response_time': response_time,
                                            'target_winner': target_winner["target_id"]},
                                   'exp_uid': exp_uid}
        processAnswer_json_response, dt = test_utils.processAnswer(processAnswer_args_dict)
        processAnswer_times += [dt]

    r = test_utils.format_times(getQuery_times, processAnswer_times, total_pulls,
                   participant_uid)
    return r


if __name__ == '__main__':
    test_api()
    # test_api(assert_200=True, num_arms=5, num_clients=10, delta=0.05,
                #    total_pulls_per_client=10, num_experiments=1)
