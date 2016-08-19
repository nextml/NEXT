import numpy
import numpy.random
import random
import json
import time
import requests
from scipy.linalg import norm
from multiprocessing import Pool
import os
import sys
try:
    import next.apps.test_utils as test_utils
except:
    sys.path.append('../../..')
    import test_utils

app_id = 'PoolBasedTripletMDS'


def test_api(assert_200=True, num_objects=5, desired_dimension=2,
            total_pulls_per_client=4, num_experiments=1, num_clients=6):
    x = numpy.linspace(0,1,num_objects)
    X_true = numpy.vstack([x,x]).transpose()

    pool = Pool(processes=num_clients)
    supported_alg_ids = ['CrowdKernel', 'RandomSampling',
                         'UncertaintySampling', 'ValidationSampling', 'STE']
    alg_list = []
    for idx, alg_id in enumerate(supported_alg_ids):
        alg_item = {}
        alg_item['alg_id'] = alg_id
        if alg_id == 'ValidationSampling':
            alg_item['alg_label'] = 'Test'
            alg_item['params'] = {'query_list': [
                [q1, q2, q3] for q1 in [0, 1, 2]
                             for q2 in [0, 1, 2]
                             for q3 in [0, 1, 2]
                                             ]}
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

    # Test POST Experiment
    initExp_args_dict = {}
    initExp_args_dict['app_id'] = 'PoolBasedTripletMDS'
    initExp_args_dict['args'] = {}
    initExp_args_dict['args']['d'] = desired_dimension
    initExp_args_dict['args']['failure_probability'] = 0.01
    initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'    #optional field
    initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
    initExp_args_dict['args']['alg_list'] = alg_list #optional field
    initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
    initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
    initExp_args_dict['args']['targets'] = {}
    initExp_args_dict['args']['targets']['n'] = num_objects

    exp_info = []
    for ell in range(num_experiments):
        initExp_response_dict, exp_uid = test_utils.initExp(initExp_args_dict)
        exp_info += [exp_uid]

    # Generate participants
    participants = []
    pool_args = []
    for i in range(num_clients):
        participant_uid = '%030x' % random.randrange(16**30)
        participants.append(participant_uid)

        experiment = numpy.random.choice(exp_info)
        exp_uid = experiment['exp_uid']
        pool_args.append( (exp_uid,participant_uid,total_pulls_per_client,X_true,assert_200) )
    results = pool.map(simulate_one_client, pool_args)

    for result in results:
        print result

    test_utils.getModel(exp_uid, app_id, supported_alg_ids, alg_list)


def simulate_one_client( input_args ):
    exp_uid,participant_uid,total_pulls,X_true,assert_200 = input_args


    getQuery_times = []
    processAnswer_times = []
    for t in range(total_pulls):
        print "Participant {1} has taken {0} pulls".format(t,participant_uid)
        # test POST getQuery #
        widget = random.choice([True] + 4*[False])
        widget = True
        getQuery_args_dict = {'args': {'participant_uid': participant_uid,
                                       'widget': widget},
                              'exp_uid': exp_uid}

        query_dict, dt = test_utils.getQuery(getQuery_args_dict)
        getQuery_times += [dt]

        if widget:
            query_dict = query_dict['args']
        query_uid = query_dict['query_uid']
        targets = query_dict['target_indices']
        #  print targets
        for target in targets:
            if target['label'] == 'center':
                index_center = target['target_id']
            elif target['label'] == 'left':
                index_left = target['target_id']
            elif target['label'] == 'right':
                index_right = target['target_id']

        ts = test_utils.response_delay()
        # sleep for a bit to simulate response time

        direction = norm(X_true[index_left]-X_true[index_center])-norm(X_true[index_right]-X_true[index_center])
        r = numpy.random.rand()
        if r<.1:
            direction = - direction
        if direction<0.:
            target_winner = index_left
        else:
            target_winner = index_right

        response_time = time.time() - ts


        # test POST processAnswer
        processAnswer_args_dict = {}
        processAnswer_args_dict["exp_uid"] = exp_uid
        processAnswer_args_dict["args"] = {}
        processAnswer_args_dict["args"]["query_uid"] = query_uid
        processAnswer_args_dict["args"]["target_winner"] = target_winner
        processAnswer_args_dict["args"]['response_time'] = response_time

        processAnswer_json_response, dt = test_utils.processAnswer(processAnswer_args_dict)
        processAnswer_times.append(dt)

    r = test_utils.format_times(getQuery_times, processAnswer_times, total_pulls,
            participant_uid)
    return r

if __name__ == '__main__':
    test_api()
    #  test_api(assert_200=False, num_objects=5, desired_dimension=2,
             #  total_pulls_per_client=100, num_experiments=1,
             #  num_clients=5, delta=0.01)
