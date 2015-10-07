"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez, chris2fernandez@gmail.com
last updated: 05/27/2015

A module for replicating the dueling bandits pure exploration experiments from the NEXT paper.

Usage:
python experiment_dueling.py
"""
import os, sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# import launch_experiment. We assume that it is located in the next-discovery top level directory.
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []
# A list of the currently available Stochastic Dueling Borda Bandit Pure Exploration algorithms
supported_alg_ids = ['BR_LilUCB','BR_Random','BR_SuccElim','BeatTheMean', 'BR_Thompson']

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

# Run algorithms here in fixed proportions
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Create experiment dictionary
cap = 'cap436'
initExp = {}
initExp['args'] = {}
initExp['args']['n'] = 25
initExp['args']['failure_probability'] = .01
initExp['args']['participant_to_algorithm_management'] = 'one_to_many' 
initExp['args']['algorithm_management_settings'] = algorithm_management_settings 
initExp['args']['alg_list'] = alg_list 
# initExp['args']['instructions'] = ''
# initExp['args']['debrief'] = ''
initExp['args']['num_tries'] = 50
initExp['app_id'] = 'DuelingBanditsPureExploration'
initExp['site_id'] = 'replace this with working site id'
initExp['site_key'] = 'replace this with working site key'

# Set the context   
experiment = {}
experiment['initExp'] = initExp
experiment['primary_type'] = 'text'
experiment['primary_target_file'] = curr_dir+"/cap436.txt"
experiment['context'] = curr_dir+"/cap436.jpg"
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

