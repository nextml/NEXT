import yaml
from numpy.random import choice,rand
from numpy import log10
import time
import numpy

import boto_conn
import os
import sys
sys.path.append("..")

try:
	MACHINE_NAME = os.environ['MACHINE_NAME']
	AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
	AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID']
	AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
	host = os.environ['NEXT_BACKEND_GLOBAL_HOST'] + \
			":" + os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
except:
	print 'The following environment variables must be defined:'

	for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
				'AWS_BUCKET_NAME', 'NEXT_BACKEND_GLOBAL_HOST','MACHINE_NAME']:
		if key not in os.environ:
			print '    ' + key
	raise

def autotune():
	filename = 'test.txt'
	benchmark = {'num_arms':5000, 'total_pulls_per_client':20,'num_clients':20, 'total_pulls':1000 }

	k=0
	while True:
		if k==0:
			config = get_config(defaults=True)
		else:
			config = get_config(defaults=False)
		k+=1
		import json
		config_str = json.dumps(config)
		stats = run_config(config_str,benchmark)
		data = {'stats':stats,'config':config,'benchmark':benchmark}
		with open(filename, "a") as myfile:
			myfile.write(json.dumps(data)+"\n")
		if True:
			S3_PATH = 'autotuning-for-next/round2'
			boto_conn.write_to_s3(local_filename_path=filename,s3_path=S3_PATH+'/'+filename)


def run_config(config_str,benchmark=None):
	import subprocess
	command = [
		'python', 'next_ec2.py',
		'--key-pair=next_key_1',
		# '--identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem',
		'--identity-file=../next_key_1.pem',
		'--custom-config=%s' % config_str,
		'rsync',
		MACHINE_NAME]
	print subprocess.check_call(command)

	command = [
		'python', 'next_ec2.py',
		'--key-pair=next_key_1',
		# '--identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem',
		'--identity-file=../next_key_1.pem',
		'docker_destroy_and_up',
		MACHINE_NAME]
	print subprocess.check_call(command)

	sleep_time = 15
	print "Sleeping for %s seconds to let master initialize..." % sleep_time
	time.sleep(sleep_time)

	import next.apps.Apps.CardinalBanditsPureExploration.tests.test_api as test_api
	if benchmark==None:
		results = test_api.test_api(num_arms=5000, total_pulls_per_client=20,num_clients=100, total_pulls=100)
	else:
		results = test_api.test_api(**benchmark)

	results.sort()
	total_pulls = len(results)
	stats = { pct:results[int(pct*total_pulls)] for pct in [.05,.5,.9,.95,.99,.999,.9999] }
	print 'getQuery\t : %f (5),    %f (50),    %f (95),    %f (99),    %f (99.9)' % (results[int(.05*total_pulls)],results[int(.50*total_pulls)],results[int(.95*total_pulls)],results[int(.99*total_pulls)],results[int(.999*total_pulls)])
	return stats

def get_config(defaults=True):
	filename = 'config.yml'
	with open(filename) as f:
		ref = yaml.load(f.read())

	config = {}
	for param in ref:
		if defaults:
			value = ref[param]['default']
		else:
			value = draw_parameter(ref[param])
		config[param] = value
	return config

def draw_parameter(cfg):
	if cfg['type']=='bool':
		return bool(choice([0,1]))
	elif cfg['type']=='int':
		if cfg['scale']=='linear':
			return choice(range(cfg['min'],cfg['max']+1))
		elif cfg['scale']=='log':
			val = cfg['min'] + 10**(rand()*log10(cfg['max']/cfg['min']))-1
			val = int(round(val))
			val = max(val,cfg['min'])
			val = min(val,cfg['max'])
			return val

if __name__ == "__main__":
	autotune()