"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez, chris2fernandez@gmail.com
modified 2015-11-24: Scott Sievert, stsievert@wisc.edu (added docs)
last updated: 2015-11-24

A module for replicating the dueling bandits pure exploration experiments from the NEXT paper.

Usage:
python experiment_dueling.py
"""

import os, sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# import launch_experiment. We assume that it is located in next/examples
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []

# A list of the currently available StochasticDuelingBanditPureExploration
# algorithms
supported_alg_ids = ['BR_LilUCB', 'BR_Random', 'BR_SuccElim',
                     'BeatTheMean', 'BR_Thompson']

# Algorithm List. These algorithms are independent (no inter-connectedness
# between algorithms) and each algorithm gets `proportion` number of queries
# (i.e., if proportions is set to 0.33 for each algorithm, each algorithm will
# sample 1/3 of the time)
alg_list = []
for alg_id in supported_alg_ids:
  alg_item = {}
  alg_item['alg_id'] = alg_id
  alg_item['alg_label'] = alg_id
  alg_item['params'] = {}
  alg_list.append(alg_item)

# Algorithm management specifies the proportion of queries coming from an
# algorithms. In this example, we specify that each algorithm recieves the same
# proportion. The alg_label's must agree with the alg_labels in the alg_list.
algorithm_management_settings = {}
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append({'alg_label': algorithm['alg_label'],
                                  'proportion':1./len(alg_list)})

# Run algorithms here in fixed proportions
# The number of queries sampled is the ones we specify, rather than using some
# more complicated scheme.
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Create experiment dictionary
initExp = {}
initExp['args'] = {}
initExp['args']['n'] = 25 # number of targets

# probability of error. similar to "significant because p < 0.05"
initExp['args']['failure_probability'] = .01

# one parcipant sees many algorithms? 'one_to_many' means one participant will
# see many algorithms
initExp['args']['participant_to_algorithm_management'] = 'one_to_many'
initExp['args']['algorithm_management_settings'] = algorithm_management_settings
initExp['args']['alg_list'] = alg_list
# initExp['args']['instructions'] = ''
# initExp['args']['debrief'] = ''
initExp['args']['num_tries'] = 50 # How many tries does each user see?

# Which app are we running? (examples of other algorithms are in examples/
initExp['app_id'] = 'DuelingBanditsPureExploration'

# which algorithms can be used? BR_LilUCB does some adaptive sampling to only
# sample the funniest captions, etc.
initExp['args']['alg_list'] = [{'alg_label': 'BR_LilUCB', 'params': {},
                                      'alg_id': 'BR_LilUCB'},
                                  {'alg_label': 'BR_Random', 'params': {},
                                      'alg_id': 'BR_Random'},
                                  {'alg_label': 'BR_SuccElim', 'params': {},
                                      'alg_id': 'BR_SuccElim'},
                                  {'alg_label': 'BeatTheMean', 'params': {},
                                      'alg_id': 'BeatTheMean'},
                                  {'alg_label': 'BR_Thompson', 'params': {},
                                      'alg_id': 'BR_Thompson'}]

# Set the context. When decided between two funny captions, the context is the
# comic the caption is for. This is static and does not change query-to-query.
experiment = {}
experiment['initExp'] = initExp
experiment['primary_type'] = 'text'
experiment['primary_target_file'] = curr_dir+"/cap436.txt"
experiment['context'] = curr_dir+"/cap436.jpg"
experiment['context_type'] = 'image'
experiment_list.append(experiment)

# Launch the experiment.
try:
  AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
  AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID']
  AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
  host = os.environ['NEXT_BACKEND_GLOBAL_HOST'] + \
            ":"+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

except:
    print 'The following environment variables must be defined:'

    for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
                'AWS_BUCKET_NAME', 'NEXT_BACKEND_GLOBAL_HOST']:
        if key not in os.environ:
            print '    ' + key

    sys.exit()


# Call launch_experiment module found in NEXT/lauch_experiment.py
exp_info = launch_experiment(host, experiment_list, AWS_ACCESS_ID,
                             AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)
exp_uid_list, exp_key_list, widget_key_list = exp_info
