import numpy
import numpy.random
import random
import json
import time
from datetime import datetime
import requests
from scipy.linalg import norm
import time
import os

HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')+':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
print HOSTNAME
def run_all(assert_200, num_clients):
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

  app_id = 'PoolBasedTripletMDS'
  
  # Setup the exp_uid's
  client_exp_uids = []
  client_exp_keys = []
  client_participant_uids = []
  for cl in range(num_clients):
    participants = []
    for i in range(10):
      participant_uid = '%030x' % random.randrange(16**30)
      participants.append(participant_uid)
    client_participant_uids.append(participants)

  # Args for the experiments
  num_objects = 30
  desired_dimension = 2
  x = numpy.linspace(0,1,num_objects)
  X_true = numpy.vstack([x,x]).transpose()
  # total_pulls = 100000*num_clients
  # total_pulls = 10*desired_dimension*num_objects*numpy.floor(numpy.log(num_objects))*num_clients*4
  total_pulls = 50

  # Generate the list of algorithms
  alg_list = []

  test_alg = {}
  test_alg['alg_id'] = 'RandomSampling'
  test_alg['alg_label'] = 'Test'
  test_alg['test_alg_label'] = 'Test'
  test_alg['params'] = {}
  alg_list.append(test_alg)

  random_alg = {}
  random_alg['alg_id'] = 'RandomSampling'
  random_alg['alg_label'] = 'Random'
  random_alg['test_alg_label'] = 'Test'
  random_alg['params'] = {}
  alg_list.append(random_alg)

  uncertainty_sampling_alg = {}
  uncertainty_sampling_alg['alg_id'] = 'UncertaintySampling'
  uncertainty_sampling_alg['alg_label'] = 'Uncertainty Sampling'
  uncertainty_sampling_alg['test_alg_label'] = 'Test'
  uncertainty_sampling_alg['params'] = {}
  alg_list.append(uncertainty_sampling_alg)

  crowd_kernel_alg = {}
  crowd_kernel_alg['alg_id'] = 'CrowdKernel'
  crowd_kernel_alg['alg_label'] = 'Crowd Kernel'
  crowd_kernel_alg['test_alg_label'] = 'Test'
  crowd_kernel_alg['params'] = {}
  alg_list.append(crowd_kernel_alg)
  
  params = {}
  test_proportion = 0.2
  params['proportions'] = []
  for algorithm in alg_list:
    if algorithm['alg_label'] == 'Test':
      params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':test_proportion }  )
    else:
      params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':(1. - test_proportion)/(len(alg_list)-1.) }  )      
  algorithm_management_settings = {}
  algorithm_management_settings['mode'] = 'fixed_proportions'
  algorithm_management_settings['params'] = params

  # args paramaters
  n = num_objects
  d = desired_dimension
  delta = 0.01

  #################################################
  # Test POST Experiment
  #################################################
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['d'] = d
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['alg_list'] = alg_list
  initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' #optional field
  initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
  initExp_args_dict['args']['alg_list'] = alg_list #optional field
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)

    exp_uid = initExp_response_dict['exp_uid']
    exp_key = initExp_response_dict['exp_key']
    client_exp_uids.append(exp_uid)
    client_exp_keys.append(exp_key)

  #################################################
  # Test GET Experiment
  #################################################
    url = "http://"+HOSTNAME+"/api/experiment/"+client_exp_uids[cl]+"/"+client_exp_keys[cl]
    response = requests.get(url)
    print "GET experiment response =",response.text, response.status_code
    if assert_200: assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)
    
  # Now we will do many get queries over a random set of exp_uid's to generate data  
  seconds_between_API_hits = .001
  t = 0
  while t<total_pulls:
    t+=1
    print t
    time.sleep(seconds_between_API_hits)

    # grab a random exp_uid
    exp_uid = client_exp_uids[t%len(client_exp_uids)] #random.choice(client_exp_uids)
    exp_key = client_exp_keys[t%len(client_exp_keys)] #random.choice(client_exp_uids)
    participant_uids = client_participant_uids[t%len(client_exp_uids)]
    participant_uid = numpy.random.choice(participants)

    #######################################
    # test GET getQuery #
    #######################################
    getQuery_args_dict = {}
    getQuery_args_dict['exp_uid'] = exp_uid
    getQuery_args_dict['exp_key'] = exp_key
    getQuery_args_dict['args'] = {}
    getQuery_args_dict['args']['participant_uid'] = participant_uid

    url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
    response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})

    print "POST getQuery response = ", response.text, response.status_code
    if assert_200: assert response.status_code is 200
    print "POST getQuery duration = ", dt
    print 

    getQuery_response_dict = json.loads(response.text)
    query_uid = getQuery_response_dict['query_uid']
    targets = getQuery_response_dict['target_indices']
    print targets
    for target in targets:
      if target['label'] == 'center':
        index_center = target['index']
      elif target['label'] == 'left':
        index_left = target['index']
      elif target['label'] == 'right':
        index_right = target['index']

    #############################################
    # test POST processAnswer 
    #############################################
    # generate simulated reward
    direction = norm(X_true[index_left]-X_true[index_center])-norm(X_true[index_right]-X_true[index_center])
    r = numpy.random.rand()
    if r<.1:
      direction = - direction
    if direction<0.:
      target_winner = index_left
    else:
      target_winner = index_right
   
    processAnswer_args_dict = {}
    processAnswer_args_dict["exp_uid"] = exp_uid
    processAnswer_args_dict["exp_key"] = exp_key
    processAnswer_args_dict["args"] = {}
    processAnswer_args_dict["args"]["query_uid"] = query_uid
    processAnswer_args_dict["args"]["target_winner"] = target_winner

    url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
    print "POST processAnswer args = ", processAnswer_args_dict
    response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
    print "POST processAnswer response", response.text, response.status_code
    if assert_200: assert response.status_code is 200
    print "POST processAnswer duration = ", dt
    print
    processAnswer_json_response = eval(response.text)

  # #############################################
  # # test GET logs 
  # #############################################
  # r = numpy.random.rand()
  # if r <.005:
  #   url = 'http://'+HOSTNAME+'/api/experiment/'+exp_uid+'/'+exp_key'/logs'
  #   response,dt = timeit(requests.get)(url)
  #   print "GET Logs response", response.text, response.status_code
  #   print "GET Logs duration = ", dt
  #   print

  # #############################################
  # # test GET participants 
  # #############################################
  # r = numpy.random.rand()
  # if r <.005:
  #   url = 'http://'+HOSTNAME+'/api/experiment/'+exp_uid+'/'+exp_key+'/participants'
  #   response,dt = timeit(requests.get)(url)
  #   print "Participants response", response.text, response.status_code
  #   print "Participants duration = ", dt
  #   print

  ############################################
  # test POST stats
  ###########################################
  # Create all our potential /experiments/stats requests and then loop over them

  args_list = []

  getStats_args_dict = {}
  getStats_args_dict['stat_id'] = 'api_activity_histogram'
  getStats_args_dict['params'] = {'task':'getQuery'}
  args_list.append(getStats_args_dict)

  getStats_args_dict = {}
  getStats_args_dict['stat_id'] = 'api_processAnswer_activity_stacked_histogram'
  getStats_args_dict['params'] = {}
  args_list.append(getStats_args_dict)

  getStats_args_dict = {}
  getStats_args_dict['stat_id'] = 'compute_duration_multiline_plot'
  getStats_args_dict['params'] = {'task':'getQuery'}
  args_list.append(getStats_args_dict)

  getStats_args_dict = {}
  getStats_args_dict['stat_id'] = 'compute_duration_detailed_stacked_area_plot'
  getStats_args_dict['params'] = {'task':'getQuery','alg_label':alg_list[-1]['alg_label']}
  args_list.append(getStats_args_dict)

  getStats_args_dict = {}
  getStats_args_dict['stat_id'] = 'test_error_multiline_plot'
  getStats_args_dict['params'] = {}
  args_list.append(getStats_args_dict)

  for cl in range(num_clients):
    getStats_args_dict = {}
    getStats_args_dict["exp_uid"] = client_exp_uids[cl]
    getStats_args_dict["exp_key"] = client_exp_keys[cl]

    for args in args_list:
      getStats_args_dict["args"] = args
      url = 'http://'+HOSTNAME+'/api/experiment/stats'
      response = requests.post(url, json.dumps(getStats_args_dict) ,headers={'content-type':'application/json'})
      getStats_json_response = eval(response.text)
      print "/experiment/stats "+args['stat_id'], str(getStats_json_response), response.status_code
      if assert_200: assert response.status_code is 200
      print 

if __name__ == '__main__':
  run_all(False,1)


