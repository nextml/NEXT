"""
This script does the following:

1. Launches an expirement
2. Tests the experiment using the computer.
3. Writes a file containing the feature vectors at each arm pull

Variables at the top of each function declare the location of

* the feature vector matrix
* the image of URLs
"""
import numpy
import numpy as np
import numpy.random
import random
import json
import time
from datetime import datetime
import requests
from scipy.linalg import norm
from scipy.io import loadmat
import time
from multiprocessing import Pool
import sys
from sklearn.preprocessing import normalize
import pickle
import os
norm = np.linalg.norm

HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')+':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

PRINT = False

def reward(x, theta, R=2):
    r = np.inner(x, theta) + R*np.random.randn()
    return r

def run_all(assert_200, home_dir='/Users/scott/', total_pulls_per_client=500,
        num_experiments=1, num_clients=1):
    """
    total_pulls_per_client: number of answers each participant gives
    num_experiments: How many experiments do we want to test?
    num_clients: Using multiprocessing library, how many simultaneous clients
    to run?
    """
    ### BEGIN params to change
    # The experiment we have launched via the `NEXT/examples/zappos/` dir
    exp_uid = '4158d26749ae14ab4191cb1c29b6b7'

    # We need X and i_star to decide what answer to give
    # the feature matrix
    X = np.load('results/features_matrix.npy')

    # the index of the "ground truth" arm
    i_star = X.shape[1] // 2
    # END parameter to tune

    num_arms = n = X.shape[1]

    # Because the filenames are in a .mat file, play with formatting them
    # names = names['Names']
    # feature_filenames = [name[0][0][0] for name in names]

    pool = Pool(processes=num_clients)

    # Testing the responses
    url = "http://"+HOSTNAME+"/api/experiment/"+exp_uid
    response = requests.get(url)
    if PRINT:
        print "GET experiment response =",response.text, response.status_code
    if assert_200: assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)
    alg_list = initExp_response_dict['args']['alg_list']
    alg_names = [alg['alg_label'] for alg in alg_list]


    # TODO: use more participants to average the errors.
    # Generate a single participant
    participant_uid = '%030x' % random.randrange(16**30)
    pool_args = [(exp_uid, participant_uid, total_pulls_per_client,
                 i_star, X, assert_200)]

    # results = pool.map(simulate_one_client, pool_args)
    results = map(simulate_one_client, pool_args)

    exp_params_to_save = results[0][1]
    print(exp_params_to_save)
    time_id = datetime.now().isoformat()[:10]
    if not time_id in os.listdir('results/'):
        os.mkdir('results/{}'.format(time_id))
    filename = 'results/{}/i_hats_{}_{}.pkl'.format(time_id, alg_names,
                                                    total_pulls_per_client)
    filename = filename.strip(' ').strip("'").strip('[').strip(']')
    print('\nWriting results to file {}\n'.format(filename))
    pickle.dump(exp_params_to_save, open(filename, 'w'))

    for result in results:
        print result



def simulate_one_client(input_args, avg_response_time=0.1):
    exp_uid, participant_uid, total_pulls, i_star, X, assert_200 = input_args

    theta_star = X[:, i_star]

    getQuery_times = []
    processAnswer_times = []
    i_hats = []
    for t in range(total_pulls):
        print "        Participant {} had {} total pulls: ".format(participant_uid, t)

        #######################################
        # test POST getQuery #
        #######################################
        getQuery_args_dict = {}
        getQuery_args_dict['exp_uid'] = exp_uid
        getQuery_args_dict['args'] = {}
        # getQuery_args_dict['args']['participant_uid'] = numpy.random.choice(participants)
        getQuery_args_dict['args']['participant_uid'] = participant_uid

        url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
        response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})
        print "POST getQuery response = ", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        print "POST getQuery duration = ", dt, "\n"
        getQuery_times.append(dt)

        query_dict = json.loads(response.text)
        if 'fail' in query_dict['meta']['status'].lower():
                print 'getQuery failed... exiting'
                sys.exit()
        query_uid = query_dict['query_uid']
        if t == 0:
            initial_indices = [query_dict['targets'][i]['index'] 
                                    for i in range(len(query_dict['targets']))]
            i_hat = random.choice(initial_indices)
            i_hat = i_star - 10
            i_hats += [i_hat]
            answer = i_hat
            answer_key = 'initial_arm'
            rewards = [1]
        else:
            # print(query_dict['targets'][0]['index'])
            # targets = query_dict['targets'][0]['index']
            i_hat = query_dict['targets'][0]['index']
            i_hats += [i_hat]
            sqrt = np.sqrt
            # decision = np.inner(X[:, i_hat], theta) + R*np.random.randn()
            answer = 1 if norm(X[:, i_star] - X[:, i_hat]) < 0.5 / sqrt(1)\
                       else -1
            # answer = np.sign(reward(X[:, i_hat], theta_star))
            rewards += [answer]
            answer_key = 'target_reward'

        # generate simulated reward #
        #############################
        # sleep for a bit to simulate response time
        ts = time.time()

        # time.sleep(    avg_response_time*numpy.random.rand()    )
        time.sleep( avg_response_time*numpy.log(1./numpy.random.rand()))
        # target_reward = true_means[i_hat] + numpy.random.randn()*0.5
        # target_reward = 1.+sum(numpy.random.rand(2)<true_means[i_hat]) # in {1,2,3}
        # target_reward = numpy.random.choice(labels)['reward']

        response_time = time.time() - ts


        #############################################
        # test POST processAnswer 
        #############################################
        processAnswer_args_dict = {}
        processAnswer_args_dict["exp_uid"] = exp_uid
        processAnswer_args_dict["args"] = {}
        processAnswer_args_dict['args']['initial_query'] = True if t==0 else False
        processAnswer_args_dict["args"]["query_uid"] = query_uid
        processAnswer_args_dict["args"]['answer'] = {answer_key: answer}
        processAnswer_args_dict["args"]['response_time'] = response_time

        url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
        print "POST processAnswer args = ", processAnswer_args_dict
        response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
        print "POST processAnswer response", response.text, response.status_code
        if assert_200: assert response.status_code is 200
        print "POST processAnswer duration = ", dt
        processAnswer_times.append(dt)
        print
        processAnswer_json_response = eval(response.text)

    exp_params_to_save = {'i_hats': i_hats,
                          'rewards': rewards,
                          'i_star': i_star}

    processAnswer_times.sort()
    getQuery_times.sort()
    return_str = '%s \n\t getQuery\t : %f (5),        %f (50),        %f (95)\n\t processAnswer\t : %f (5),        %f (50),        %f (95)\n' % (participant_uid,getQuery_times[int(.05*total_pulls)],getQuery_times[int(.50*total_pulls)],getQuery_times[int(.95*total_pulls)],processAnswer_times[int(.05*total_pulls)],processAnswer_times[int(.50*total_pulls)],processAnswer_times[int(.95*total_pulls)])
    return return_str, exp_params_to_save


def timeit(f):
    """ 
    Utility used to time the duration of code execution. This script can be composed with any other script.

    Usage::\n
        def f(n): 
            return n**n    

        def g(n): 
            return n,n**n 

        answer0,dt = timeit(f)(3)
        answer1,answer2,dt = timeit(g)(3)
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
    run_all(False)
