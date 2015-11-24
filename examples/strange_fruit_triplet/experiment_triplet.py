import os, sys

# The line below imports launch_experiment.py.
# We assume that it is located in next/examples
# This function is used at the very bottom of this file
sys.path.append("../")
from launch_experiment import *

experiment_list = []

# List of Algorithms currently available for this app type
alg_ids = ['RandomSampling','RandomSampling','UncertaintySampling','CrowdKernel','STE']

# Algorithm List. These algorithms are independent (no inter-connectedness
# between algorithms) and each algorithm gets `proportion` number of queries
# (i.e., if proportions is set to 0.33 for each algorithm, each algorithm will
# sample 1/3 of the time)
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

# Algorithm management specifies the proportion of queries coming from an
# algorithms. In this example, we specify that each algorithm recieves the same
# proportion. The alg_label's must agree with the alg_labels in the alg_list.
params = {}
params['proportions'] = []
for algorithm in alg_list:
    params['proportions'].append({'alg_label': algorithm['alg_label'] ,'proportion':1./len(alg_list)})

# Run algorithms here in fixed proportions
# The number of queries sampled is the ones we specify, rather than using some
# more complicated scheme.
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

# The user chooses between two images. This could be text or video as well.
experiment['primary_type'] = 'image'
experiment['primary_target_file'] = '{}/strangefruit30.zip'.format(curr_dir)
experiment_list.append(experiment)

# Launch the experiment
try:
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
    host = os.environ['NEXT_BACKEND_GLOBAL_HOST']+ ":" \
            + os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
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
