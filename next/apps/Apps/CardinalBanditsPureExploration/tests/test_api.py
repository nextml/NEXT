import numpy as np
import numpy.random
import random
import json
import time
import requests
from multiprocessing import Pool
import sys
sys.path.append('../../../../../')
import next.utils as utils
import os

HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost') + \
           ':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

def test_api(assert_200=True, num_arms=5, total_pulls_per_client=10,
             num_experiments=1, num_clients=4, total_pulls=10, verbose=True):
  true_means = numpy.array(range(num_arms)[::-1])/float(num_arms)
  pool = Pool(processes=num_clients)           

  # setup algorithms
  supported_alg_ids = ['LilUCB', 'RoundRobin']
  alg_list = []
  for i, alg_id in enumerate(supported_alg_ids):
    alg_item = {'alg_id': alg_id, 'alg_label': alg_id+'_'+str(i)}
    alg_list.append(alg_item)
  algorithm_management_settings = {'mode': 'fixed_proportions',
                                   'params': [  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  for algorithm in alg_list]}

  #################################################
  # Test POST Experiment
  #################################################
  initExp_args_dict = {}
  initExp_args_dict['app_id'] = 'CardinalBanditsPureExploration'
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['targets'] = {'n':num_arms}
  initExp_args_dict['args']['failure_probability'] = .05
  initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'  #optional field
  initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
  initExp_args_dict['args']['alg_list'] = alg_list #optional field
  initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
  initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
  initExp_args_dict['args']['context_type'] = 'text'
  initExp_args_dict['args']['context'] = 'This is a context'
  initExp_args_dict['args']['rating_scale'] = {'labels':[{'label':'bad','reward':1.},{'label':'neutral','reward':2.},{'label':'good','reward':3.}]}

  exp_info = []
  for ell in range(num_experiments):
    #################################################
    # Test initExp
    #################################################

    response = requests.post("http://"+HOSTNAME+"/api/experiment",
                             json.dumps(initExp_args_dict),
                             headers={'content-type':'application/json'})
    print "POST initExp response =", response.text, response.status_code
    if assert_200: assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)
    if 'fail' in initExp_response_dict['meta']['status'].lower():
        print 'The experiment initialization failed... exiting'
        sys.exit()
    exp_uid = initExp_response_dict['exp_uid']
    exp_info.append( {'exp_uid':exp_uid} )
    #################################################
    # Test GET Experiment
    #################################################
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
    exp_uid = numpy.random.choice(exp_info)['exp_uid']
    pool_args.append( (exp_uid, participant_uid, total_pulls_per_client, total_pulls, true_means,assert_200, verbose) )
  results = pool.map(simulate_one_client, pool_args)

  for result in results:
    print "result = ", result


def simulate_one_client(input_args):
  exp_uid, participant_uid, total_pulls_per_client, total_pulls, true_means, assert_200, verbose = input_args
  avg_response_time = 0.2
  time.sleep(  2*avg_response_time*numpy.log(1./numpy.random.rand())  )
  getQuery_times = []
  processAnswer_times = []
  print "{} total pulls (looping over this many items)".format(total_pulls)
  for t in range(total_pulls):
    if (t % total_pulls_per_client) == 0:
      participant_uid = '%030x' % random.randrange(16**30)
      print "participant uid = ", participant_uid
    if verbose: print "    Participant {} had {} total pulls: ".format(participant_uid, t)

    #######################################
    # test POST getQuery #
    #######################################
    getQuery_args_dict = {'exp_uid':exp_uid, 'args':{'participant_uid':participant_uid}}
    response,dt = utils.timeit(requests.post)('http://'+HOSTNAME+'/api/experiment/getQuery',
                                        json.dumps(getQuery_args_dict),
                                        headers={'content-type':'application/json'})
    if verbose: print "POST getQuery response = ", response.text, response.status_code
    if assert_200: assert response.status_code is 200
    if verbose: print "POST getQuery duration = ", dt
    getQuery_times.append(dt)
    
    query_dict = json.loads(response.text)
    query_uid = query_dict['query_uid']
    targets = query_dict['target_indices']
    target_index = targets[0]['target']['target_id']

    # generate simulated reward #
    #############################
    # sleep for a bit to simulate response time
    ts = time.time()
    # time.sleep(  avg_response_time*numpy.random.rand()  )
    time.sleep(  avg_response_time*numpy.log(1./numpy.random.rand())  )
    # target_reward = true_means[target_index] + numpy.random.randn()*0.5
    target_reward = 1.+sum(numpy.random.rand(2)<true_means[target_index]) # in {1,2,3}
    # target_reward = numpy.random.choice(labels)['reward']
    response_time = time.time() - ts

    #############################################
    # test POST processAnswer 
    #############################################
    processAnswer_args_dict = {}
    processAnswer_args_dict["exp_uid"] = exp_uid
    processAnswer_args_dict["args"] = {}
    processAnswer_args_dict["args"]["query_uid"] = query_uid
    target_reward = str(target_reward) if np.random.randint(2) == 0 else target_reward
    processAnswer_args_dict["args"]['target_reward'] = str(target_reward)
    processAnswer_args_dict["args"]['response_time'] = response_time
    if verbose: print "POST processAnswer args = ", processAnswer_args_dict
    response,dt = utils.timeit(requests.post)('http://'+HOSTNAME+'/api/experiment/processAnswer',
                                        json.dumps(processAnswer_args_dict),
                                        headers={'content-type':'application/json'})
    if verbose: print "POST processAnswer response", response.text, response.status_code
    if assert_200: assert response.status_code is 200
    if verbose: print "POST processAnswer duration = ", dt
    processAnswer_times.append(dt)
    if verbose: print
  processAnswer_times.sort()
  getQuery_times.sort()
  print '%s \n\t getQuery\t : %f (5),    %f (50),    %f (95)\n\t processAnswer\t : %f (5),    %f (50),    %f (95)\n' % (participant_uid,getQuery_times[int(.05*total_pulls)],getQuery_times[int(.50*total_pulls)],getQuery_times[int(.95*total_pulls)],processAnswer_times[int(.05*total_pulls)],processAnswer_times[int(.50*total_pulls)],processAnswer_times[int(.95*total_pulls)])
  return getQuery_times,processAnswer_times


if __name__ == '__main__':
  print HOSTNAME
  #  test_api()
  test_api(assert_200=True, num_arms=50, total_pulls_per_client=100,
        num_experiments=1, num_clients=10, total_pulls=10000)
