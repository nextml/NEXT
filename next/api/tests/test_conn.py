import sys
import httplib
import urllib
import json
import time
import os
import numpy
import json
import requests
from multiprocessing import Pool

# HOSTNAME = "ec2-52-24-223-179.us-west-2.compute.amazonaws.com:8001"
HOSTNAME = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')+':'+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

def run_all():
	n = int(50)

	# print simulate_one_client( (n,0) )
	num_clients = 50
	client_args = []
	for cl in range(num_clients):
		client_args.append( (n,cl) )

	try:
		pool = Pool(processes=num_clients)  
		results = pool.map(simulate_one_client, client_args )
		pool.terminate()
		pool.join()
	except KeyboardInterrupt:
		pool.terminate()
		pool.join()
		return
	except Exception, e:
		pool.terminate()
		pool.join()

	for result in results:
		print result


def simulate_one_client( input_args ):
	n,participant_uid = input_args
	avg_response_time = 1.

	rtt = []
	for i in range(n):
		data = json.dumps({'num_database_actions':10})
		url =  'http://'+HOSTNAME+'/widgets/testconn'
		ts = time.time()
		response = requests.post(url,data,headers={'content-type':'application/json'})
		te = time.time()
		data = response.text
		data_dict = eval(data)
		rtt.append(te-ts)
		print "requests %d  %s   %.4f" % (i, str(data_dict), te-ts)
		time.sleep(  avg_response_time*numpy.log(1/numpy.random.rand())  )

	rtt.sort()
	return_str = '%s \t rtt\t : %f (5),    %f (50),    %f (95)' % (participant_uid,rtt[int(.05*len(rtt))],rtt[int(.50*len(rtt))],rtt[int(.95*len(rtt))])
	return return_str

if __name__ == '__main__':
	print HOSTNAME
	run_all()