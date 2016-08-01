import numpy
import numpy.random
import random
import json
import time
import requests
from scipy.linalg import norm
from multiprocessing import Pool
try:
    from next.utils import timeit
except:
    raise Exception('Must be run under pytest. Example use `cd path/to/test_api.py; '
                    'py.test test_api.py. Use `py.test -s test_api.py` to '
                    'view stdout')


import os
HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')+':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

def test_api(assert_200=True, num_objects=20, desired_dimension=2,
                        total_pulls_per_client=40, num_experiments=1, num_clients=5):

    true_weights = numpy.zeros(desired_dimension)
    true_weights[0] = 1.

    pool = Pool(processes=num_clients)
    supported_alg_ids = ['RandomSamplingLinearLeastSquares','RandomSamplingLinearLeastSquares']

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
                        'meta': {'features':features}})

    #################################################
    # Test POST Experiment
    #################################################
    print '\n'*2 + 'Testing POST initExp...'
    initExp_args_dict = {}
    initExp_args_dict['app_id'] = 'PoolBasedBinaryClassification'
    initExp_args_dict['args'] = {}
    initExp_args_dict['args']['failure_probability'] = 0.01
    initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'    #optional field
    initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
    initExp_args_dict['args']['alg_list'] = alg_list #optional field
    initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
    initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
    initExp_args_dict['args']['targets'] = {}
    initExp_args_dict['args']['targets']['targetset'] = targetset

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
        # Test GET Experiment
        #################################################
        print '\n'*2 + 'Testing GET initExp...'
        url = "http://"+HOSTNAME+"/api/experiment/"+exp_uid
        response = requests.get(url)
        print "GET experiment response =",response.text, response.status_code
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
        pool_args.append((exp_uid,participant_uid,total_pulls_per_client,true_weights,assert_200))
    print "participants are", participants
    results = pool.map(simulate_one_client, pool_args)

    for result in results:
        print result


def simulate_one_client(input_args):
    exp_uid, participant_uid, total_pulls, true_weights, assert_200 = input_args
    avg_response_time = 1.0

    getQuery_times = []
    processAnswer_times = []
    for t in range(total_pulls):

        print t, participant_uid
        #######################################
        # test POST getQuery #
        #######################################
        print '\n'*2 + 'Testing POST getQuery...'
        getQuery_args_dict = {}
        getQuery_args_dict['exp_uid'] = exp_uid
        getQuery_args_dict['args'] = {}
        getQuery_args_dict['args']['participant_uid'] = participant_uid

        url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
        response, dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type': 'application/json'})
        print "POST getQuery response = ", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        print "POST getQuery duration = ", dt, "\n"
        getQuery_times.append(dt)

        query_dict = json.loads(response.text)
        print "query_dict: ", query_dict
        print(query_dict.keys())
        query_uid = query_dict['query_uid']
        target = query_dict['target_indices']
        x = numpy.array(eval(target['primary_description']))
        print target

        # generate simulated reward #
        #############################
        # sleep for a bit to simulate response time
        ts = time.time()

        time.sleep(avg_response_time*numpy.log(1./numpy.random.rand()))
        target_label = numpy.sign(numpy.dot(x,true_weights))
        

        response_time = time.time() - ts


        #############################################
        # test POST processAnswer
        #############################################
        print '\n'*2 + 'Testing POST processAnswer...'
        processAnswer_args_dict = {}
        processAnswer_args_dict["exp_uid"] = exp_uid
        processAnswer_args_dict["args"] = {}
        processAnswer_args_dict["args"]["query_uid"] = query_uid
        processAnswer_args_dict["args"]["target_label"] = target_label
        processAnswer_args_dict["args"]['response_time'] = response_time

        url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
        print "POST processAnswer args = ", processAnswer_args_dict
        response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
        print "POST processAnswer response", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        print "POST processAnswer duration = ", dt, "\n"
        processAnswer_times.append(dt)
        processAnswer_json_response = eval(response.text)

    processAnswer_times.sort()
    getQuery_times.sort()
    return_str = '%s \n\t getQuery\t : %f (5),        %f (50),        %f (95)\n\t processAnswer\t : %f (5),        %f (50),        %f (95)\n' % (participant_uid,getQuery_times[int(.05*total_pulls)],getQuery_times[int(.50*total_pulls)],getQuery_times[int(.95*total_pulls)],processAnswer_times[int(.05*total_pulls)],processAnswer_times[int(.50*total_pulls)],processAnswer_times[int(.95*total_pulls)])
    return return_str


if __name__ == '__main__':
    print HOSTNAME
    test_api()
    #    test_api(assert_200=False, num_objects=100, desired_dimension=4,
                     #    total_pulls_per_client=30, num_experiments=1, num_clients=10,
                     #    delta=0.01)
