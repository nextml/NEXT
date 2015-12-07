"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez, chris2fernandez@gmail.com
modified 2015-11-24: Scott Sievert, stsievert@wisc.edu (added docs)
last updated: 2015-11-24

A module for replicating the tuple bandits pure exploration experiments from the NEXT paper.

Usage:
python experiment_tuple.py
"""
import os, sys

# The line below imports launch_experiment.py.
# We assume that it is located in next/examples
# This function is used at the very bottom of this file
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

# Algorithm List. These algorithms are independent (no inter-connectedness
# between algorithms) and each algorithm gets `proportion` number of queries
# (i.e., if proportions is set to 0.33 for each algorithm, each algorithm will
# sample 1/3 of the time)
algorithm_management_settings = {}
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )

# Algorithm management specifies the proportion of queries coming from an
# algorithms. In this example, we specify that each algorithm recieves the same
# proportion. The alg_label's must agree with the alg_labels in the alg_list.
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Select some cartoons from the curr_dir
cap_list = ['cap431','cap438','cap436']

# Create experiment dictionary
for cap in cap_list:
    initExp = {}
    initExp['args'] = {}
    initExp['args']['n'] = 8 # number of targets
    initExp['args']['k'] = 8 # how many choices does the user have?

    # probability of error. similar to "significant because p < 0.05"
    initExp['args']['failure_probability'] = .01

    # one parcipant sees many algorithms? 'one_to_many' means one participant
    # will see many algorithms
    initExp['args']['participant_to_algorithm_management'] = 'one_to_many' # 'one_to_one'
    initExp['args']['algorithm_management_settings'] = algorithm_management_settings
    initExp['args']['alg_list'] = alg_list

    # What does the user see at start and finish? These are the
    # instructions/debreif (by default they have default values)
    # initExp['args']['instructions'] = ''
    # initExp['args']['debrief'] =''

    initExp['args']['num_tries'] = 3 # number of quesitons does the user sees

    # Which app are we running? (examples of other algorithms are in examples/
    initExp['app_id'] = 'TupleBanditsPureExploration'

    # Set the context and targets
    experiment = {}
    experiment['initExp'] = initExp
    # what type are we chooisng from? Can be text, image, video (beta as of
    # 2015-11) or audio (experimental as of 2015-11)
    experiment['primary_type'] = 'text'
    experiment['primary_target_file'] = curr_dir+"/"+cap+".txt"

    # What's the context? In this example, this is the comic that we're asking
    # to find the funniest caption for.
    experiment['context'] = curr_dir+"/"+cap+".jpg"
    experiment['context_type'] = 'image'
    experiment_list.append(experiment)

# Launch the experiment
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

# Update the cartoon_dueling.html file wit the exp_uid_list and widget_key_list
# with open('cartoon_tuple.html','r') as page:
#   print "opended file"
#   page_string = page.read()
#   page_string = page_string.replace("{{exp_uid_list}}", str(exp_uid_list))
#   page_string = page_string.replace("{{widget_key_list}}", str(widget_key_list))
#   with open('../../next_frontend_base/next_frontend_base/templates/cartoon_tuple.html','w') as out:
#     out.write(page_string)
#     out.flush()
#     out.close()
