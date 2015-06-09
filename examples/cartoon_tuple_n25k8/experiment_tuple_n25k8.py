"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez, chris2fernandez@gmail.com
last updated: 05/27/2015

A module for replicating the 25 total arms with 8 arms shown at a time tuple bandits pure exploration 
experiments from the NEXT paper.

Usage:
python experiment_tuple_n25k8.py
"""
import os, sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# import launch_experiment. We assume that it is located in the next-discovery top level directory.
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []
supported_alg_ids = ['RandomSampling']

# Create common alg_list
alg_list = []
for alg_id in supported_alg_ids:
  alg_item = {}
  alg_item['alg_id'] = alg_id
  alg_item['alg_label'] = alg_id
  alg_item['params'] = {}
  alg_list.append(alg_item)

# Create common algorithm management settings  
algorithm_management_settings = {}
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )

# Algorithms are run here in fixed proportions
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Select some cartoons from the curr_dir
# cap_list = ['cap431','cap438','cap436']
cap_list = ['cap436']

# Create experiment dictionary
for cap in cap_list:
  initExp = {}
  initExp['args'] = {}
  # if cap == cap_list[2]:
  #   initExp['args']['n'] = 25
  # else:
  #   initExp['args']['n'] = 8
  initExp['args']['n'] = 25    
  initExp['args']['k'] = 8
  initExp['args']['failure_probability'] = .01
  initExp['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'  
  initExp['args']['algorithm_management_settings'] = algorithm_management_settings 
  initExp['args']['alg_list'] = alg_list 
  # initExp['args']['instructions'] = ''
  # initExp['args']['debrief'] =''
  # initExp['args']['num_tries'] = 3
  initExp['args']['num_tries'] = 1
  initExp['app_id'] = 'TupleBanditsPureExploration'
  initExp['site_id'] = 'replace this with working site id'
  initExp['site_key'] = 'replace this with working site key'

# Set the context
  experiment = {}
  experiment['initExp'] = initExp
  experiment['target_file'] = curr_dir+"/"+cap+".txt"
  experiment['context'] = curr_dir+"/"+cap+".jpg"
  experiment['context_type'] = 'image'
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

# Call launch_experiment module found in NEXT/lauch_experiment.py
exp_uid_list, exp_key_list, widget_key_list = launch_experiment(host, experiment_list, AWS_ACCESS_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)

# Update the cartoon_dueling.html file wit the exp_uid_list and widget_key_list
# with open('cartoon_tuple_n25k8.html','r') as page:
#   print "opended file"
#   page_string = page.read()
#   page_string = page_string.replace("{{exp_uid_list}}", str(exp_uid_list))
#   page_string = page_string.replace("{{widget_key_list}}", str(widget_key_list))
#   with open('../../next_frontend_base/next_frontend_base/templates/cartoon_tuple_n25k8.html','w') as out:
#     out.write(page_string)
#     out.flush()
#     out.close()
