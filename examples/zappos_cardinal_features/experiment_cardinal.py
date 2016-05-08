import os, sys
from collections import OrderedDict
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from scipy.io import loadmat
import numpy as np
import numpy
from sklearn.preprocessing import normalize
import pickle


# filename = '/Users/scott/Dropbox/image_search_scott/Features/features_allshoes_8_normalized.mat'
input_dir = 'parse-output/N=100_M=20/'
filename = input_dir + 'Zappos_Caffe_Layer8.mat'
X = loadmat(filename)['X']

# X \in {num_features x num_arms}
# num_features, num_arms = (2, 4)
num_features, num_arms = X.shape
n = num_arms

# X = np.random.rand(num_features, num_arms)
# X = normalize(X, axis=0)
# X = X[:num_features, :num_arms]
# X = np.zeros((num_features, num_arms))
# X[0] = [0, 1, 2, 3]
feature_filenames = pickle.load(open(input_dir + 'filenames.pkl', 'rb'))

images = input_dir + 'AllShoes.zip'

delta = 0.05
supported_alg_ids = ['OFUL']

labels = [{'label':'no', 'reward':1.0},
          {'label':'yes','reward':2.0}]
R = 2.0

true_means = numpy.array(range(num_arms)[::-1]) / float(num_arms)
total_pulls_per_client = 200

# The line below imports launch_experiment.py.
# We assume that it is located in next/examples
# This function is used at the very bottom of this file
sys.path.append("../")
from launch_experiment import *

curr_dir = os.path.dirname(os.path.abspath(__file__))
experiment_list = []

# algs in next/apps/Apps/CardinalBanditsPureExploration/algs/
supported_alg_ids = ['OFUL']

# Algorithm List. These algorithms are independent (no inter-connectedness
# between algorithms) and each algorithm gets `proportion` number of queries
# (i.e., if proportions is set to 0.33 for each algorithm, each algorithm will
# sample 1/3 of the time)
alg_list = []
for alg_id in supported_alg_ids:
    alg_item = {}
    alg_item['alg_id'] = alg_id
    alg_item['alg_label'] = alg_id
    if alg_id == 'OFUL':
        theta_star = np.random.randn(X.shape[0])
        theta_star /= np.linalg.norm(theta_star)
        alg_item['params'] = {'X': X.tolist(),
                              'theta_star': theta_star.tolist()}
    else:
        alg_item['params'] = {}

    alg_list.append(alg_item)

# Algorithm management specifies the proportion of queries coming from an
# algorithms. In this example, we specify that each algorithm recieves the same
# proportion. The alg_label's must agree with the alg_labels in the alg_list.
algorithm_management_settings = {}
params = []
#params['proportions'] = []
for algorithm in alg_list:
    #params['proportions'].append({'alg_label': algorithm['alg_label'] ,
                                    #'proportion':1./len(alg_list)})
    params += [{'alg_label': algorithm['alg_label'],
                               'proportion': 1.0 / len(alg_list)}]

print(params)
# Run algorithms here in fixed proportions
# The number of queries sampled is the ones we specify, rather than using some
# more complicated scheme.
algorithm_management_settings['mode'] = 'fixed_proportions'
algorithm_management_settings['params'] = params

# Create experiment dictionary
cap = 'cap436'
initExp = {}
initExp['args'] = {} # arguments to pass the algorithm

# What's the probabiity of error? Similar to "similar because p < 0.05"
initExp['args']['failure_probability'] = .05
initExp['args']['R'] = .5
initExp['args']['rating_scale'] = {'labels': labels}

# one parcipant sees many algorithms? 'one_to_many' means one participant will
# see many algorithms
initExp['args']['participant_to_algorithm_management'] = 'one_to_many'
initExp['args']['algorithm_management_settings'] = algorithm_management_settings
initExp['args']['alg_list'] = alg_list

initExp['args']['num_tries'] = 50 # How many tries does each user see?
initExp['args']['feature_filenames'] = feature_filenames

# Which app are we running? (examples of other algorithms are in examples/
initExp['app_id'] = 'CardinalBanditsFeatures'

experiment = {}
experiment['initExp'] = initExp

# When presented with a query, the user will rate a text object
experiment['primary_type'] = 'image'
experiment['primary_target_file'] = curr_dir+'/' + images

# Set the context. This is the static image that the user sees. i.e., trying to
# determine the funniest caption of a single comic, the context is the comic.
# experiment['context'] = 'Choose something'
# experiment['context_type'] = 'text'
experiment_list.append(experiment)

# Launch the experiment
try:
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
    host = os.environ['NEXT_BACKEND_GLOBAL_HOST'] + \
            ":" + os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
except:
    print('The following environment variables must be defined:')

    for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
                'AWS_BUCKET_NAME', 'NEXT_BACKEND_GLOBAL_HOST']:
        if key not in os.environ:
            print('    ' + key)

    sys.exit()

# Call launch_experiment module (found in NEXT/lauch_experiment.py)
exp_uid_list = launch_experiment(host, experiment_list, AWS_ACCESS_ID,
                                 AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)

