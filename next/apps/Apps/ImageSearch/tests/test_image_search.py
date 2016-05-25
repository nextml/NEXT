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

HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')+':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

PRINT = False

def run_all(assert_200, home_dir='/Users/scott/', total_pulls_per_client=5,
        num_experiments=1, num_clients=1):
    """
    total_pulls_per_client: number of answers each participant gives
    num_experiments: How many experiments do we want to test?
    num_clients: Using multiprocessing library, how many simultaneous clients
    to run?
    """
    # feature matrix
    features_matrix_url = 'https://dl.dropboxusercontent.com/u/9160935/features_allshoes_8_normalized.mat'

    # The filenames of the images to each filename
    names = loadmat('/Users/scott/Desktop/Rudi-features-matlab/ColorLabel_new.mat')
    names = names['Names']
    feature_filenames = [name[0][0][0] for name in names]

    # the locations of the images
    image_urls_file = 'urls-50k-launch-python.csv'

    # for testing purposes only
    num_arms = n = 100
    feature_filenames = feature_filenames[:num_arms]

    # this experiment will only be performed over one experiment
    supported_alg_ids = ['OFUL']#, 'RandomSampling']

    # the index of the "ground truth" arm
    i_star = num_arms // 2
    X = loadmat(home_dir + 'Desktop/Rudi-features-matlab/features_allshoes_8_normalized.mat')['features_all']

    app_id = 'ImageSearch'

    # loading the filenames of which columns in feature_matrix correspond
    # to which images
    # input_dir =
    # '/Users/scott/Developer/NEXT/examples/zappos_cardinal_features/'
    # feature_filenames = pickle.load(open(input_dir + 'filenames.pkl', 'rb'))

    # num_features, num_arms = (2, 400)    # X \in {num_features x num_arms}

    # X = np.random.rand(num_features, num_arms)
    # X = normalize(X, axis=0)
    # X = X[:num_features, :num_arms]
    # print "X \in R^{}".format(X.shape)

    true_means = numpy.array(range(num_arms)[::-1]) / float(num_arms)

    pool = Pool(processes=num_clients)


    # input test parameters
    # n = num_arms
    delta = 0.05

    labels = [{'label':'no','reward':-1.}, {'label':'yes','reward':1.}]

    alg_list = []
    for i, alg_id in enumerate(supported_alg_ids):
        alg_item = {}
        alg_item['alg_id'] = alg_id
        alg_item['alg_label'] = alg_id+'_'+str(i)
        # if 'OFUL' in supported_alg_ids:
            # theta_star = np.random.randn(X.shape[0])
            # theta_star /= np.linalg.norm(theta_star)
            # print(X.shape)
        alg_item['params'] = {}#{'X':X.tolist(), 'theta_star':theta_star.tolist() }
        #alg_item['params'] = {}
        alg_list.append(alg_item)
    params = []
    #params['proportions'] = []
    for algorithm in alg_list:
        params.append(    { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }    )
    algorithm_management_settings = {}
    algorithm_management_settings['mode'] = 'fixed_proportions'
    algorithm_management_settings['params'] = params

    # print algorithm_management_settings

    #################################################
    # Test POST Experiment
    #################################################
    initExp_args_dict = {}
    initExp_args_dict['args'] = {}

    initExp_args_dict['args']['features'] = features_matrix_url
    initExp_args_dict['args']['feature_filenames'] = feature_filenames
    initExp_args_dict['args']['targets'] = {'n':n}
    initExp_args_dict['args']['failure_probability'] = delta
    initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'    #optional field
    initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
    initExp_args_dict['args']['alg_list'] = alg_list #optional field
    initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
    initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
    initExp_args_dict['args']['context_type'] = 'text'
    initExp_args_dict['args']['context'] = 'This is a context'
    initExp_args_dict['args']['rating_scale'] = {'labels':labels}
    initExp_args_dict['app_id'] = app_id

    exp_info = []
    for ell in range(num_experiments):
        url = "http://"+HOSTNAME+"/api/experiment"
        response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
        if PRINT:
            print "POST initExp response =", response.text, response.status_code

        if assert_200: assert response.status_code is 200
        initExp_response_dict = json.loads(response.text)
        if 'fail' in initExp_response_dict['meta']['status'].lower():
                print initExp_response_dict
                print 'The experiment initialization failed... exiting'
                sys.exit()

        exp_uid = initExp_response_dict['exp_uid']

        exp_info.append( {'exp_uid':exp_uid,} )

        #################################################
        # Test GET Experiment
        #################################################
        url = "http://"+HOSTNAME+"/api/experiment/"+exp_uid
        response = requests.get(url)
        if PRINT:
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
        pool_args.append((exp_uid, participant_uid, total_pulls_per_client,
                          i_star, X, assert_200))

    # results = pool.map(simulate_one_client, pool_args)
    results = map(simulate_one_client, pool_args)

    exp_params_to_save = results[0][1]
    print(exp_params_to_save)
    exp_params_to_save['features_matrix_url'] = features_matrix_url
    time_id = datetime.now().isoformat()[:10]
    if not time_id in os.listdir('results/'):
        os.mkdir('results/{}'.format(time_id))
    filename = 'results/{}/i_hats_{}.pkl'.format(time_id, supported_alg_ids)
    filename = filename.strip(' ').strip("'").strip('[').strip(']')
    print('\nWriting results to file {}\n'.format(filename))
    pickle.dump(exp_params_to_save, open(filename, 'w'))

    for result in results:
        print result



def simulate_one_client(input_args):
    exp_uid, participant_uid, total_pulls, i_star, X, assert_200 = input_args
    avg_response_time = 1.

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
            i_hats += [i_hat]
            answer = i_hat
            answer_key = 'initial_arm'
        else:
            # print(query_dict['targets'][0]['index'])
            # targets = query_dict['targets'][0]['index']
            i_hat = query_dict['targets'][0]['index']
            i_hats += [i_hat]
            answer = 1 if random.random() > 0.5 else -1
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
