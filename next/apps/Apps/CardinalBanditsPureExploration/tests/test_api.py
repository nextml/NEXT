import numpy
import numpy as np
import numpy.random
import random
import json
import time
from datetime import datetime
import requests
from scipy.linalg import norm
import time
from multiprocessing import Pool
import sys

import os
HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost') + \
					 ':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
app_id = 'CardinalBanditsPureExploration'


def test_api(assert_200=True, num_arms=10, total_pulls_per_client=20,
             num_experiments=1, num_clients=20, total_pulls=10):

	#  num_arms = 50
	true_means = numpy.array(range(num_arms)[::-1])/float(num_arms)
	#  total_pulls_per_client = 100

	#  num_experiments = 1

	# clients run in simultaneous fashion using multiprocessing library
	#  num_clients = 10
	#  total_pulls = 10         


	# input test parameters
	n = num_arms
	delta = 0.05
	supported_alg_ids = ['LilUCB']

	labels = [{'label':'bad','reward':1.},{'label':'neutral','reward':2.},{'label':'good','reward':3.}]

	alg_list = []
	for i, alg_id in enumerate(supported_alg_ids):
		alg_item = {}
		alg_item['alg_id'] = alg_id
		alg_item['alg_label'] = alg_id+'_'+str(i)
		#alg_item['params'] = {}
		alg_list.append(alg_item)
	params = []
	#params['proportions'] = []
	for algorithm in alg_list:
		params.append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )
	algorithm_management_settings = {}
	algorithm_management_settings['mode'] = 'fixed_proportions'
	algorithm_management_settings['params'] = params

	print "alg mangement settings", algorithm_management_settings


	#################################################
	# Test POST Experiment
	#################################################
	initExp_args_dict = {}
	initExp_args_dict['args'] = {}

	initExp_args_dict['args']['targets'] = {'n':n}
	initExp_args_dict['args']['failure_probability'] = delta
	initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'  #optional field
	initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
	initExp_args_dict['args']['alg_list'] = alg_list #optional field
	initExp_args_dict['args']['instructions'] = 'You want instructions, here are your test instructions'
	initExp_args_dict['args']['debrief'] = 'You want a debrief, here is your test debrief'
	initExp_args_dict['args']['context_type'] = 'text'
	initExp_args_dict['args']['context'] = 'This is a context'
	initExp_args_dict['args']['rating_scale'] = {'labels':labels}
	#  initExp_args_dict['args']['HAHA'] = {'labels':labels}
	initExp_args_dict['app_id'] = app_id

	exp_info = []
	for ell in range(num_experiments):
		url = "http://"+HOSTNAME+"/api/experiment"
		response = requests.post(url, json.dumps(initExp_args_dict), headers={'content-type':'application/json'})
		print "POST initExp response =",response.text, response.status_code

		if assert_200:
				assert response.status_code is 200
		initExp_response_dict = json.loads(response.text)
		if 'fail' in initExp_response_dict['meta']['status'].lower():
				print 'The experiment initialization failed... exiting'
				sys.exit()

		exp_uid = initExp_response_dict['exp_uid']

		exp_info.append( {'exp_uid':exp_uid,} )

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
	while True:
		try:
			pool = Pool(processes=num_clients)
			break
		except:
			time.sleep(5)  

	for i in range(num_clients):
		participant_uid = '%030x' % random.randrange(16**30)
		participants.append(participant_uid)

		experiment = numpy.random.choice(exp_info)
		exp_uid = experiment['exp_uid']
		pool_args.append( (exp_uid,participant_uid,total_pulls_per_client,total_pulls,true_means,assert_200) )

	results = pool.map(simulate_one_client, pool_args)

	all_results = []
	for result in results:
		all_results.extend(result[0])

        # Test loading the dashboard
        dashboard_url = ("http://" + HOSTNAME + "/dashboard"
                         "/experiment_dashboard/{}/{}".format(exp_uid, app_id))

        stats_url = ("http://" + HOSTNAME + "/dashboard"
                     "/experiment_dashboard/{}/{}".format(exp_uid, app_id))
        for url in [dashboard_url, stats_url]:
                response = requests.get(url)
                if assert_200: assert response.status_code is 200

	return all_results



def simulate_one_client(input_args):
	exp_uid,participant_uid,total_pulls_per_client,total_pulls,true_means,assert_200 = input_args
	avg_response_time = 0.2
	verbose = False
	num_fails = 0

	time.sleep(  2*avg_response_time*numpy.log(1./numpy.random.rand())  )

	getQuery_times = []
	processAnswer_times = []
	print "{} total pulls (looping over this many items)".format(total_pulls)
	for t in range(total_pulls):
		if (t % total_pulls_per_client) == 0:
			participant_uid = '%030x' % random.randrange(16**30)
			print "participant uid = ", participant_uid


		if verbose: print "    Participant {} had {} total pulls: ".format(participant_uid, t)

		try:
			#######################################
			# test POST getQuery #
			#######################################
                        widget = random.choice([True] + 4*[False])
                        getQuery_args_dict = {'exp_uid': exp_uid,
                                              'args': {'participant_uid':
                                                  participant_uid,
                                                       'widget': widget}}
			# getQuery_args_dict['args']['participant_uid'] = numpy.random.choice(participants)
			getQuery_args_dict['args']['participant_uid'] = participant_uid

			url = 'http://'+HOSTNAME+'/api/experiment/getQuery'
			response,dt = timeit(requests.post)(url, json.dumps(getQuery_args_dict),headers={'content-type':'application/json'})
			if verbose: print "POST getQuery response = ", response.text, response.status_code
			if assert_200: assert response.status_code is 200
			if verbose: print "POST getQuery duration = ", dt
			getQuery_times.append(dt)
			if verbose: print 
			

			query_dict = json.loads(response.text)
                        if widget:
                                query_dict = query_dict['args']
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

			url = 'http://'+HOSTNAME+'/api/experiment/processAnswer'
			if verbose: print "POST processAnswer args = ", processAnswer_args_dict
			response,dt = timeit(requests.post)(url, json.dumps(processAnswer_args_dict), headers={'content-type':'application/json'})
			if verbose: print "POST processAnswer response", response.text, response.status_code
			if assert_200: assert response.status_code is 200
			if verbose: print "POST processAnswer duration = ", dt
			processAnswer_times.append(dt)
			if verbose: print
			processAnswer_json_response = eval(response.text)
		except:
			getQuery_times.append(1000.)
			processAnswer_times.append(1000.)
			num_fails = num_fails+1
			if num_fails > 5:
				getQuery_times = [1000.]*total_pulls
				processAnswer_times = [1000.]*total_pulls
				break
			else:
				time.sleep( 5*numpy.log(1./numpy.random.rand()) )

	processAnswer_times.sort()
	getQuery_times.sort()
	print '%s \n\t getQuery\t : %f (5),    %f (50),    %f (95)\n\t processAnswer\t : %f (5),    %f (50),    %f (95)\n' % (participant_uid,getQuery_times[int(.05*len(getQuery_times))],getQuery_times[int(.50*len(getQuery_times))],getQuery_times[int(.95*len(getQuery_times))],processAnswer_times[int(.05*len(processAnswer_times))],processAnswer_times[int(.50*len(processAnswer_times))],processAnswer_times[int(.95*len(processAnswer_times))])

	return getQuery_times,processAnswer_times




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
	#  test_api()
	test_api()
