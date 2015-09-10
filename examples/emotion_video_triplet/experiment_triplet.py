# Stored video targets: 
import os, sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []
supported_alg_ids = ['RandomSampling','CrowdKernel']

# Create common alg_list
alg_list = []
for idx,alg_id in enumerate(supported_alg_ids):
  alg_item = {}
  alg_item['alg_id'] = alg_id
  if idx==0:
    alg_item['alg_label'] = 'Test'
  else:
    alg_item['alg_label'] = alg_id    
  alg_item['test_alg_label'] = 'Test'
  alg_item['params'] = {}
  alg_list.append(alg_item)

# Create common algorithm management settings  
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )

algorithm_management_settings = {}
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Create experiment dictionary
initExp = {}
initExp['args'] = {}
initExp['args']['n'] = 43
initExp['args']['d'] = 2
initExp['args']['failure_probability'] = .05
initExp['args']['participant_to_algorithm_management'] = 'one_to_many' 
initExp['args']['algorithm_management_settings'] = algorithm_management_settings 
initExp['args']['alg_list'] = alg_list 
initExp['args']['instructions'] = 'On each trial, pick the facial expression on the bottom that conveys the same feeling as the one on the top.'
initExp['args']['debrief'] = 'Thanks for participating!'
initExp['app_id'] = 'PoolBasedTripletMDS'
# initExp['site_id'] = 'replace this with working site id'
# initExp['site_key'] = 'replace this with working site key'
initExp['args']['num_tries'] = 50

experiment = {}
experiment['initExp'] = initExp
experiment['target_file'] = curr_dir + "/video_targets.zip"
print "target_file", curr_dir + "/video_targets.zip"
experiment_list.append(experiment)

# Launch the experiment
try:
  AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
  AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID']
  AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
  host = os.environ['NEXT_BACKEND_GLOBAL_HOST']+":"+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
except:
  print "You must set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, NEXT_BACKEND_GLOBAL_HOST as environment variables"
  sys.exit()
exp_uid_list, exp_key_list, widget_key_list = launch_experiment(host, experiment_list, AWS_ACCESS_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)

