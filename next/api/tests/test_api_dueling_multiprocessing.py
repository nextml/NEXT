import numpy
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
HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')+':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

def run_all(assert_200):

  app_id = 'DuelingBanditsPureExploration'
  num_arms = 300
  true_means = numpy.array(range(num_arms))/float(num_arms)
  total_pulls_per_client = 10

  num_experiments = 1

  # clients run in simultaneous fashion using multiprocessing library
  num_clients = 500

  pool = Pool(processes=num_clients)           


  # input test parameters
  n = num_arms
  delta = 0.05
  supported_alg_ids = ['BR_LilUCB_b2','BR_Random_b2','BR_Thompson_b2']

  alg_list = []
  for alg_id in supported_alg_ids:
    alg_item = {}
    alg_item['alg_id'] = alg_id
    alg_item['alg_label'] = alg_id
    alg_item['params'] = {}
    alg_list.append(alg_item)
  params = {}
  params['proportions'] = []
  for algorithm in alg_list:
    params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )
  algorithm_management_settings = {}
  algorithm_management_settings['mode'] = 'fixed_proportions'
  algorithm_management_settings['params'] = params



  #################################################
  # Test POST Experiment
  #################################################
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'  #optional field
  initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
  initExp_args_dict['args']['alg_list'] = alg_list #optional field
  initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
  initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
  initExp_args_dict['args']['context_type'] = 'text'
  initExp_args_dict['args']['context'] = 'Boom baby dueling works'
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
    exp_key = initExp_response_dict['exp_key']

    exp_info.append( {'exp_uid':exp_uid,'exp_key':exp_key} )

    #################################################
    # Test GET Experiment
    #################################################
    url = "http://"+HOSTNAME+"/api/experiment/"+exp_uid+"/"+exp_key
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
    exp_key = experiment['exp_key']
    pool_args.append( (exp_uid,exp_key,participant_uid,total_pulls_per_client,true_means,assert_200) )

  results = pool.map(simulate_one_client, pool_args)

  for result in results:
    print result


def simulate_one_client( input_args ):
  exp_uid,exp_key,participant_uid,total_pulls,true_means,assert_200 = input_args
  avg_response_time = 1.


  getQuery_times = []
  processAnswer_times = []
  for t in range(total_pulls):
    

    print t,participant_uid
    #######################################
    # test POST getQuery #
    #######################################
    getQuery_args_dict = {}
    getQuery_args_dict['exp_uid'] = exp_uid
    getQuery_args_dict['exp_key'] = exp_key
    getQuery_args_dict['args'] = {}
    # getQuery_args_dict['args']['participant_uid'] = numpy.random.choice(participants)
    getQuery_args_dict['args']['participant_uid'] = participant_uid

    url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
    response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})
    print "POST getQuery response = ", response.text, response.status_code
    if assert_200: assert response.status_code is 200
    print "POST getQuery duration = ", dt
    getQuery_times.append(dt)
    print 
    

    query_dict = json.loads(response.text)
    query_uid = query_dict['query_uid']
    targets = query_dict['target_indices']
    for target in targets:
      if target['label'] == 'left':
        index_left = target['index']
      if target['label'] == 'right':
        index_right = target['index']
      if target['flag'] == 1:
        index_painted = target['index']

    # generate simulated reward #
    #############################
    # sleep for a bit to simulate response time
    ts = time.time()

    time.sleep(  avg_response_time*numpy.random.rand()  )
    reward_left = true_means[index_left] + numpy.random.randn()*0.5
    reward_right = true_means[index_right] + numpy.random.randn()*0.5
    if reward_left>reward_right:
      index_winner = index_left
    else:
      index_winner = index_right

    response_time = time.time() - ts


    #############################################
    # test POST processAnswer 
    #############################################
    processAnswer_args_dict = {}
    processAnswer_args_dict["exp_uid"] = exp_uid
    processAnswer_args_dict["exp_key"] = exp_key
    processAnswer_args_dict["args"] = {}
    processAnswer_args_dict["args"]["query_uid"] = query_uid
    processAnswer_args_dict["args"]['target_winner'] = index_winner
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

  processAnswer_times.sort()
  getQuery_times.sort()
  return_str = '%s \n\t getQuery\t : %f (5),    %f (50),    %f (95)\n\t processAnswer\t : %f (5),    %f (50),    %f (95)\n' % (participant_uid,getQuery_times[int(.05*total_pulls)],getQuery_times[int(.50*total_pulls)],getQuery_times[int(.95*total_pulls)],processAnswer_times[int(.05*total_pulls)],processAnswer_times[int(.50*total_pulls)],processAnswer_times[int(.95*total_pulls)])
  return return_str



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
