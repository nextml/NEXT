from __future__ import print_function
import numpy
import numpy.random
import random
import json
import time
import requests
from scipy.linalg import norm
from multiprocessing import Pool
import os, sys
try:
    import next.apps.test_utils as test_utils
except:
    file_dir = '/'.join(__file__.split('/')[:-1])
    sys.path.append('{}/../../../next/apps'.format(file_dir))
    import test_utils


app_id = 'PoolBasedBinaryClassification'

def test_api(assert_200=True, num_objects=4, desired_dimension=1,
                        total_pulls_per_client=5, num_experiments=1,
                        num_clients=7):
    true_weights = numpy.zeros(desired_dimension)
    true_weights[0] = 1.
    pool = Pool(processes=num_clients)
    supported_alg_ids = ['RandomSamplingLinearLeastSquares',
                         'RandomSamplingLinearLeastSquares',
                         'RoundRobin']
    alg_list = []
    for idx,alg_id in enumerate(supported_alg_ids):
        alg_item = {}
        alg_item['alg_id'] = alg_id
        if idx==0:
            alg_item['alg_label'] = 'Test'
        else:
            alg_item['alg_label'] = alg_id
        alg_item['test_alg_label'] = 'Test'
        alg_list.append(alg_item)
    params = []
    for algorithm in alg_list:
        params.append({'alg_label': algorithm['alg_label'],
                       'proportion': 1./len(alg_list)})

    algorithm_management_settings = {}
    algorithm_management_settings['mode'] = 'fixed_proportions'
    algorithm_management_settings['params'] = params

    targetset = []
    for i in range(num_objects):
        features = list(numpy.random.randn(desired_dimension))
        targetset.append({'primary_description': str(features),
                        'primary_type':'text',
                        'alt_description':'%d' % (i),
                        'alt_type':'text',
                        'target_id': str(i),
                        'meta': {'features':features}})

    # Test POST Experiment
    print('\n'*2 + 'Testing POST initExp...')
    initExp_args_dict = {}
    initExp_args_dict['app_id'] = 'PoolBasedBinaryClassification'
    initExp_args_dict['args'] = {}
    initExp_args_dict['args']['failure_probability'] = 0.01
    initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'    #optional field
    initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
    initExp_args_dict['args']['alg_list'] = alg_list #optional field
    initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
    initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
    initExp_args_dict['args']['targets'] = {'targetset': targetset}

    exp_info = []
    for ell in range(num_experiments):
        initExp_response_dict, exp_info_ = test_utils.initExp(initExp_args_dict)
        exp_info += [exp_info_]
        exp_uid = initExp_response_dict['exp_uid']

        exp_info.append({'exp_uid':exp_uid,})

        # Test GET Experiment
        initExp_response_dict = test_utils.getExp(exp_uid)

    # Generate participants
    ###################################

    participants = []
    pool_args = []
    for i in range(num_clients):
        participant_uid = '%030x' % random.randrange(16**30)
        participants.append(participant_uid)

        experiment = numpy.random.choice(exp_info)
        exp_uid = experiment['exp_uid']
        pool_args.append((exp_uid,participant_uid,total_pulls_per_client,true_weights,assert_200))

    print("participants are", participants)
    results = pool.map(simulate_one_client, pool_args)

    for result in results:
        print(result)

    test_utils.getModel(exp_uid, app_id, supported_alg_ids, alg_list)


def simulate_one_client(input_args):
    exp_uid, participant_uid, total_pulls, true_weights, assert_200 = input_args

    getQuery_times = []
    processAnswer_times = []
    for t in range(total_pulls):

        print("participant {} had {} pulls".format(participant_uid, t))

        # test POST getQuery #
        widget = True
        getQuery_args_dict = {'args': {'participant_uid': participant_uid,
                                       'widget': widget},
                              'exp_uid': exp_uid}

        query_dict, dt = test_utils.getQuery(getQuery_args_dict)
        getQuery_times += [dt]

        if widget:
            query_dict = query_dict['args']
        query_uid = query_dict['query_uid']
        target = query_dict['target_indices']
        x = numpy.array(eval(target['primary_description']))

        # generate simulated reward #
        # sleep for a bit to simulate response time
        ts = test_utils.response_delay()
        target_label = numpy.sign(numpy.dot(x,true_weights))
        response_time = time.time() - ts

        # test POST processAnswer
        processAnswer_args_dict = {}
        processAnswer_args_dict["exp_uid"] = exp_uid
        processAnswer_args_dict["args"] = {}
        processAnswer_args_dict["args"]["query_uid"] = query_uid
        processAnswer_args_dict["args"]["target_label"] = target_label
        processAnswer_args_dict["args"]['response_time'] = response_time

        processAnswer_json_response, dt = test_utils.processAnswer(processAnswer_args_dict)
        processAnswer_times += [dt]

    return_str = test_utils.format_times(getQuery_times, processAnswer_times,
                                         total_pulls, participant_uid)
    return return_str


if __name__ == '__main__':
    test_api()
    #    test_api(assert_200=False, num_objects=100, desired_dimension=4,
                     #    total_pulls_per_client=30, num_experiments=1, num_clients=10,
                     #    delta=0.01)
