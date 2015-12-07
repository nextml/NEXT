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

# The line below imports launch_experiment.py.
# We assume that it is located in next/examples
# This function is used at the very bottom of this file
sys.path.append("../")
from launch_experiment import *

# List of Algorithms currently available for TupleBandits
curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []
supported_alg_ids = ['RandomSampling']

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

# Run algorithms here in fixed proportions
# The number of queries sampled is the ones we specify, rather than using some
# more complicated scheme.
algorithm_management_settings = {}
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )

# Algorithms are run here in fixed proportions
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Select some cartoons from the curr_dir
cap_list = ['cap436']

# Create experiment dictionary
for cap in cap_list:
    initExp = {}
    initExp['args'] = {}
    # if cap == cap_list[2]:
    #   initExp['args']['n'] = 25
    # else:
    #   initExp['args']['n'] = 8
    initExp['args']['n'] = 25 # number of targets
    initExp['args']['k'] = 8 # how many choices does the user have to choose among?

    # probability of error. similar to "significant because p < 0.05"
    initExp['args']['failure_probability'] = .01

    # one parcipant sees many algorithms? 'one_to_many' means one participant
    # will see many algorithms
    initExp['args']['participant_to_algorithm_management'] = 'one_to_many'
    initExp['args']['algorithm_management_settings'] = algorithm_management_settings
    initExp['args']['alg_list'] = alg_list

    # What does the user see at start and finish? These are the
    # instructions/debreif (by default they have default values)
    # initExp['args']['instructions'] = ''
    # initExp['args']['debrief'] =''
    initExp['args']['num_tries'] = 1 # how many questions does the user see?

    # Which app are we running? (examples of other algorithms are in examples/
    # (this is another TupleBandits example)
    initExp['app_id'] = 'TupleBanditsPureExploration'

    # Set the context
    experiment = {}
    experiment['initExp'] = initExp
    experiment['primary_type'] = 'text'
    experiment['primary_target_file'] = curr_dir+"/"+cap+".txt"
    experiment['target_file'] = curr_dir+"/"+cap+".txt"
    experiment['context'] = curr_dir+"/"+cap+".jpg"
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
