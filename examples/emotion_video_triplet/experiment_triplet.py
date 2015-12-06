# Stored video targets:
import os, sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# The line below imports launch_experiment.py.
# We assume that it is located in next/examples
# This function is used at the very bottom of this file
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []

# List of Algorithms currently available for this particular app
supported_alg_ids = ['RandomSampling','CrowdKernel']

# Algorithm List. These algorithms are independent (no inter-connectedness
# between algorithms) and each algorithm gets `proportion` number of queries
# (i.e., if proportions is set to 0.33 for each algorithm, each algorithm will
# sample 1/3 of the time)
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

# Algorithm management specifies the proportion of queries coming from an
# algorithms. In this example, we specify that each algorithm recieves the same
# proportion. The alg_label's must agree with the alg_labels in the alg_list.
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list) }  )

# Run algorithms here in fixed proportions
# The number of queries sampled is the ones we specify, rather than using some
# more complicated scheme.
algorithm_management_settings = {}
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Create experiment dictionary
initExp = {}
initExp['args'] = {}
initExp['args']['n'] = 43 # how many targets?
initExp['args']['d'] = 2 # how many dimensions to embed in?

# probability of error. similar to "significant because p < 0.05"
initExp['args']['failure_probability'] = .05

# one parcipant sees many algorithms? 'one_to_many' means one participant
# will see many algorithms. 'one_to_many' is the other option
initExp['args']['participant_to_algorithm_management'] = 'one_to_many'

initExp['args']['algorithm_management_settings'] = algorithm_management_settings
initExp['args']['alg_list'] = alg_list

# What does the user see at start and finish? These are the instructions/debreif
# (they have default values)
initExp['args']['instructions'] = 'On each trial, pick the facial expression on the bottom that conveys the same feeling as the one on the top.'
initExp['args']['debrief'] = 'Thanks for participating!'

# what app are we running?
initExp['app_id'] = 'PoolBasedTripletMDS'
# initExp['site_id'] = 'replace this with working site id' # TODO: remove
# initExp['site_key'] = 'replace this with working site key' # TODO: remove
initExp['args']['num_tries'] = 50 # how many questions does one use see?

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
    host = os.environ['NEXT_BACKEND_GLOBAL_HOST'] + \
            ":"+os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
except:
    print 'The following environment variables must be defined:'

    for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
                'AWS_BUCKET_NAME', 'NEXT_BACKEND_GLOBAL_HOST']:
        if key not in os.environ:
            print '    ' + key

    sys.exit()
exp_info = launch_experiment(host, experiment_list, AWS_ACCESS_ID,
                             AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)
exp_uid_list, exp_key_list, widget_key_list = exp_info
