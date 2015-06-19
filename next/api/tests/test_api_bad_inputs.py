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
  # num_clients = 1
  # assert_200 = True

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
  num_objects = 100
  desired_dimension = 2
  x = numpy.linspace(0,1,num_objects)
  X_true = numpy.vstack([x,x]).transpose()
  # total_pulls = 100000*num_clients
  total_pulls = 3

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
  # Test POST Experiment with no app id
  #################################################
  print
  print 'Test POST Experiment with no app id'
  print
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['d'] = d
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['alg_list'] = alg_list
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert int(response.status_code) == 400
    initExp_response_dict = json.loads(response.text)

  #################################################
  # Test POST Experiment with empty args
  #################################################
  print
  print 'Test POST Experiment with empty args'
  print
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert int(response.status_code) == 400
    initExp_response_dict = json.loads(response.text)    

  #################################################
  # Test POST Experiment with letter for numerical value (failure_probability)
  #################################################  
  print
  print 'Test POST Experiment with letter for numerical value (failure_probability)'
  print
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['d'] = d
  initExp_args_dict['args']['failure_probability'] = 'Failure Prob'
  initExp_args_dict['args']['alg_list'] = alg_list
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    # This is a problem! 200 is returned each time
    # if assert_200: assert response.status_code == 400
    initExp_response_dict = json.loads(response.text)

  #################################################
  # Test POST Experiment with letter for numerical value (dimension)
  #################################################  
  print
  print 'Test POST Experiment with letter for numerical value (dimension)'
  # print
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['d'] = 'Huge Dimension'
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['alg_list'] = alg_list
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert response.status_code == 400
    initExp_response_dict = json.loads(response.text)    

  #################################################
  # Test POST Experiment with letter for numerical value (num objects)
  #################################################  
  print
  print 'Test POST Experiment with letter for numerical value (num objects)'
  print
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = 'Huge Number of Objects'
  initExp_args_dict['args']['d'] = d
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['alg_list'] = alg_list
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert response.status_code == 400
    initExp_response_dict = json.loads(response.text)  

  #################################################
  # Test POST Experiment with empty alg_list
  #################################################
  print
  print 'Test POST Experiment with empty alg_list'
  print  
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['d'] = d
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['alg_list'] = []
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert response.status_code == 200
    initExp_response_dict = json.loads(response.text)

  #################################################
  # Test POST Experiment with no optional fields present
  #################################################
  print
  print 'Test POST Experiment with no optional fields present'
  print  
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['d'] = d
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['alg_list'] = alg_list
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'

  for cl in range(num_clients):
    # convert python dictionary to json dictionary
    url = "http://"+HOSTNAME+"/api/experiment"
    response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
    print "POST initExp response =",response.text, response.status_code
    if assert_200: assert response.status_code == 200
    initExp_response_dict = json.loads(response.text)

    exp_uid = initExp_response_dict['exp_uid']
    exp_key = initExp_response_dict['exp_key']
    client_exp_uids.append(exp_uid)
    client_exp_keys.append(exp_key)

  #################################################
  # Test GET Experiment
  #################################################
  print
  print 'Test POST Experiment with no optional fields present'
  print  
  url = "http://"+HOSTNAME+"/api/experiment/"+client_exp_uids[cl]+"/"+client_exp_keys[cl]
  response = requests.get(url)
  print "GET experiment response =",response.text, response.status_code
  if assert_200: assert response.status_code is 200
  initExp_response_dict = json.loads(response.text)
  print
    
  # Now we will do many get queries over a random set of exp_uid's to generate data  
  seconds_between_API_hits = .001
  t = 0
  while t<total_pulls:
    t+=1
    # print t
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
    if t == 3: 
      getQuery_args_dict['args']['participant_uid'] = 'fake participant_uid'
      print
      print 'Test GET getQuery with fake participant_uid'
      print 

      url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
      response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})

      print "POST getQuery response = ", response.text, response.status_code
      # This should not be 200
      if assert_200: assert response.status_code is 400
      print "POST getQuery duration = ", dt
      print 

    else:
      url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
      response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})

      print "POST getQuery response = ", response.text, response.status_code
      if assert_200: assert response.status_code is 200
      print "POST getQuery duration = ", dt
      print 

    getQuery_response_dict = json.loads(response.text)
    query_uid = getQuery_response_dict['query_uid']
    targets = getQuery_response_dict['target_indices']
    # print targets
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

    if t == 1: 
      processAnswer_args_dict["args"]["query_uid"] = ''
      print
      print 'test POST processAnswer with empty query_uid'
      print

      processAnswer_args_dict["args"]["target_winner"] = target_winner
      url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
      print "POST processAnswer args = ", processAnswer_args_dict
      response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
      print "POST processAnswer response", response.text, response.status_code
      if assert_200: assert response.status_code is 400
      print "POST processAnswer duration = ", dt
      print
      processAnswer_json_response = eval(response.text)

    elif t == 2: 
      processAnswer_args_dict["args"]["target_winner"] = ''
      print
      print 'test POST processAnswer with empty target_winner'
      print

      url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
      print "POST processAnswer args = ", processAnswer_args_dict
      response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
      print "POST processAnswer response", response.text, response.status_code
      # This should not be 200
      if assert_200: assert response.status_code is 400
      print "POST processAnswer duration = ", dt
      print
      processAnswer_json_response = eval(response.text)

    else:
      url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
      print "POST processAnswer args = ", processAnswer_args_dict
      response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
      print "POST processAnswer response", response.text, response.status_code
      if assert_200: assert response.status_code is 200
      print "POST processAnswer duration = ", dt
      print
      processAnswer_json_response = eval(response.text)

if __name__ == '__main__':
  run_all()

