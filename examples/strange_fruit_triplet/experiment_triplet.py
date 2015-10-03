import os, sys
# import launch_experiment. We assume that it is located in the next-discovery top level directory.
sys.path.append("../")
from launch_experiment import *


experiment_list = []

# Algorithms that we will test against
alg_ids = ['RandomSampling','RandomSampling','UncertaintySampling','CrowdKernel','STE']

# Create common alg_list
alg_list = []
for idx,alg_id in enumerate(alg_ids):
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
    params['proportions'].append({'alg_label': algorithm['alg_label'] ,'proportion':1./len(alg_list)})

algorithm_management_settings = {}
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params


# Create experiment dictionary
initExp = {}
initExp['args'] = {}
initExp['args']['n'] = 30
initExp['args']['d'] = 2
initExp['args']['failure_probability'] = .01
initExp['args']['participant_to_algorithm_management'] = 'one_to_many' 
initExp['args']['algorithm_management_settings'] = algorithm_management_settings 
initExp['args']['alg_list'] = alg_list
initExp['args']['instructions'] = 'Test instructions'
initExp['args']['debrief'] = 'Test debrief'

initExp['app_id'] = 'PoolBasedTripletMDS'
initExp['site_id'] = 'replace this with working site id'
initExp['site_key'] = 'replace this with working site key'


curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment = {}
experiment['initExp'] = initExp
experiment['primary_type'] = 'image'
experiment['primary_target_file'] = '{}/strangefruit30.zip'.format(curr_dir)
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
