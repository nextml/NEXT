"""
author: Lalit Jain lalitkumarjj@gmail.com
modified 05/27/2015: Chris Fernandez, chris2fernandez@gmail.com
modified 2015-11-24: Scott Sievert, stsievert@wisc.edu (added docs)
last updated: 2015-11-24

A module for replicating the dueling bandits pure exploration experiments from
the NEXT paper.

Usage:
python experiment_dueling.py
"""

import os, sys
from collections import OrderedDict
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# The line below imports launch_experiment.py.
# We assume that it is located in next/examples
# This function is used at the very bottom of this file
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []

# List of Algorithms currently available for
# StochasticDuelingBanditPureExploration algorithms
supported_alg_ids = ['RandomSampling',
                     'LilUCB']

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
    params['proportions'].append({'alg_label': algorithm['alg_label'] ,
                                    'proportion':1./len(alg_list)})

# Run algorithms here in fixed proportions
# The number of queries sampled is the ones we specify, rather than using some
# more complicated scheme.
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Create experiment dictionary
initExp = {}
initExp['args'] = {} # arguments to pass the algorithm
initExp['args']['n'] = 25 # items in target set

# What's the probabiity of error? Similar to "similar because p < 0.05"
initExp['args']['failure_probability'] = .05
initExp['args']['R'] = 1.
initExp['args']['labels'] =[{'label':'unfunny', 'reward':1},
                            {'label':'somewhat funny', 'reward':2},
                            {'label':'funny', 'reward':3}]

# one parcipant sees many algorithms? 'one_to_many' means one participant will
# see many algorithms
initExp['args']['participant_to_algorithm_management'] = 'one_to_many'
initExp['args']['algorithm_management_settings'] = algorithm_management_settings
initExp['args']['alg_list'] = alg_list

initExp['args']['num_tries'] = 1e5 # How many tries does each user see?

# Which app are we running? (examples of other algorithms are in examples/
initExp['app_id'] = 'CardinalBanditsPureExploration'

experiment = {}
experiment['initExp'] = initExp

# When presented with a query, the user will rate a text object
experiment['primary_type'] = 'text'
experiment['primary_target_file'] = curr_dir+"/captions.txt"

# Set the context. This is the static image that the user sees. i.e., trying to
# determine the funniest caption of a single comic, the context is the comic.
experiment['context'] = curr_dir+"/cartoon.jpg"
experiment['context_type'] = 'image'
experiment_list.append(experiment)

# Launch the experiment
try:
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
    host = os.environ['NEXT_BACKEND_GLOBAL_HOST'] + \
            ":" + os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
except:
    print 'The following environment variables must be defined:'

    for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
                'AWS_BUCKET_NAME', 'NEXT_BACKEND_GLOBAL_HOST']:
        if key not in os.environ:
            print '    ' + key

    sys.exit()

# Call launch_experiment module (found in NEXT/lauch_experiment.py)
exp_info = launch_experiment(host, experiment_list, AWS_ACCESS_ID,
                             AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)

exp_uid_list, exp_key_list, widget_key_list = exp_info
