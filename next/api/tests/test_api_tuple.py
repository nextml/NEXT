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

def run_all(assert_200):
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

  #HOSTNAME= '52.11.148.214:8001'

  app_id = 'TupleBanditsPureExploration'

  num_arms = 10
  num_objects_to_display = 4
  true_means = numpy.array(range(num_arms))/float(num_arms)
  total_pulls = 10*num_arms
  # total_pulls = 50

  # rm = ResourceManager()

  # print
  # print utils.get_app_about(app_id)
  # print

  # # get all the relevant algs
  # supported_alg_ids = utils.get_app_supported_algs(app_id)
  # print
  # print "supported_alg_ids : " + str(supported_alg_ids)
  # print

  supported_alg_ids = ['RandomSampling']

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


  # input test parameters
  n = num_arms
  k = num_objects_to_display
  delta = 0.01

  participants = []
  for i in range(10):
    participant_uid = '%030x' % random.randrange(16**30)
    participants.append(participant_uid)

  ########################
  #
  # Test initExp
  initExp_args_dict = {}
  initExp_args_dict['args'] = {}
  initExp_args_dict['args']['n'] = n
  initExp_args_dict['args']['k'] = k
  initExp_args_dict['args']['failure_probability'] = delta
  initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'  #optional field
  initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
  initExp_args_dict['args']['alg_list'] = alg_list #optional field
  initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
  initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
  initExp_args_dict['args']['context_type'] = 'text'
  initExp_args_dict['args']['context'] = 'Boom baby tuple works'
  initExp_args_dict['app_id'] = app_id
  initExp_args_dict['site_id'] = 'replace this with working site id'
  initExp_args_dict['site_key'] = 'replace this with working site key'


  url = "http://"+HOSTNAME+"/api/experiment"
  response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
  print "POST initExp response =",response.text, response.status_code
  initExp_response_dict = json.loads(response.text)

  exp_uid = initExp_response_dict['exp_uid']
  exp_key = initExp_response_dict['exp_key']

  url = "http://"+HOSTNAME+"/api/experiment/"+exp_uid+"/"+exp_key
  response = requests.get(url)
  print "GET experiment response =",response.text, response.status_code
  initExp_response_dict = json.loads(response.text)

  # url = "http://"+HOSTNAME+"/widgets/temp-widget-keys"
  # args_dict={ 'exp_uid':exp_uid,
  #             'exp_key':exp_key,
  #             'n':1, #number of widget keys
  #             'tries':1000,
  #             'duration':10000 }
  # print "temp-widget-keys = " + str(args_dict)
  # response = requests.post(url, json.dumps(args_dict),headers={'content-type':'application/json'})
  # widget_key_dict = json.loads(response.text)
  # widget_keys = widget_key_dict['keys']
  # print "POST temp-widget-keys response = ", response.text, response.status_code

  for t in range(total_pulls):

    # time.sleep(.001)
    print t
    # test getQuery #
    #################

    getQuery_args_dict = {}
    getQuery_args_dict['exp_uid'] = exp_uid
    getQuery_args_dict['exp_key'] = exp_key
    getQuery_args_dict['args'] = {}
    getQuery_args_dict['args']['participant_uid'] = numpy.random.choice(participants)

    url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
    response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})
    print "POST getQuery response = ", response.text, response.status_code
    print "POST getQuery duration = ", dt
    print 

    query_dict = json.loads(response.text)
    print query_dict
    query_uid = query_dict['query_uid']
    targets = query_dict['target_indices']

    # generate simulated reward #
    #############################
    rewards = numpy.zeros(len(targets)).tolist()
    for i, target_index in enumerate(targets):
      rewards[i] = true_means[target_index['index']] + numpy.random.randn()*0.5

    target_winner = targets[numpy.argmax(rewards)]['target']['target_id']

    # test processAnswer #
    #####################
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
    print "POST processAnswer duration = ", dt
    print
    processAnswer_json_response = eval(response.text)


  # test getStats #
  #################

  # args_list = []

  # getStats_args_dict = {}
  # getStats_args_dict['stat_id'] = 'most_current_ranking'
  # getStats_args_dict['params'] = {'alg_label':'RandomSampling'}

  # args_list.append(getStats_args_dict)

  # getStats_args_dict = {}
  # getStats_args_dict["exp_uid"] = exp_uid
  # getStats_args_dict["exp_key"] = exp_key

  # for args in args_list:
  #   getStats_args_dict["args"] = args
  #   url = 'http://'+HOSTNAME+'/api/experiment/stats'
  #   response = requests.post(url, json.dumps(getStats_args_dict) ,headers={'content-type':'application/json'})
  #   getStats_json_response = eval(response.text)
  #   print "/experiment/stats "+args['stat_id'], str(getStats_json_response), response.status_code
  #   print 

  print "%s : All tests compeleted successfully" % (app_id)

  if __name__ == '__main__':
    run_all(False)
