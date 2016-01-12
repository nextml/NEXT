
import random
import numpy
import yaml
import json

def PoolBasedTripletMDS_dict():
    app_id = 'PoolBasedTripletMDS'

    # Setup the exp_uid's
    client_exp_uids = []
    client_exp_keys = []
    client_participant_uids = []
    num_clients = 50
    for cl in range(num_clients):
        participants = []
        for i in range(10):
            participant_uid = '%030x' % random.randrange(16**30)
            participants.append(participant_uid)
        client_participant_uids.append(participants)

    # Args for the experiments
    num_objects = 30
    desired_dimension = 2
    x = numpy.linspace(0,1,num_objects)
    X_true = numpy.vstack([x,x]).transpose()
    # total_pulls = 100000*num_clients
    # total_pulls = 10*desired_dimension*num_objects*numpy.floor(numpy.log(num_objects))*num_clients*4
    total_pulls = 50

    # Generate the list of algorithms
    alg_list = []

    test_alg = {}
    test_alg['alg_id'] = 'RandomSampling'
    test_alg['alg_label'] = 'Test'
    test_alg['test_alg_label'] = 'Test'
    test_alg['params'] = {}
    alg_list.append(test_alg)

    random_alg = {}
    random_alg['alg_id'] = 'RandomSampling'
    random_alg['alg_label'] = 'Random'
    random_alg['test_alg_label'] = 'Test'
    random_alg['params'] = {}
    alg_list.append(random_alg)

    uncertainty_sampling_alg = {}
    uncertainty_sampling_alg['alg_id'] = 'UncertaintySampling'
    uncertainty_sampling_alg['alg_label'] = 'Uncertainty Sampling'
    uncertainty_sampling_alg['test_alg_label'] = 'Test'
    uncertainty_sampling_alg['params'] = {}
    alg_list.append(uncertainty_sampling_alg)

    crowd_kernel_alg = {}
    crowd_kernel_alg['alg_id'] = 'CrowdKernel'
    crowd_kernel_alg['alg_label'] = 'Crowd Kernel'
    crowd_kernel_alg['test_alg_label'] = 'Test'
    crowd_kernel_alg['params'] = {}
    alg_list.append(crowd_kernel_alg)

    params = {}
    test_proportion = 0.2
    params['proportions'] = []
    for algorithm in alg_list:
        if algorithm['alg_label'] == 'Test':
            params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':test_proportion }  )
        else:
            params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':(1. - test_proportion)/(len(alg_list)-1.) }  )
    algorithm_management_settings = {}
    algorithm_management_settings['mode'] = 'fixed_proportions'
    algorithm_management_settings['params'] = params

    # args paramaters
    n = num_objects
    d = desired_dimension
    delta = 0.01

    #################################################
    # Test POST Experiment
    #################################################
    initExp_args_dict = {}
    initExp_args_dict['args'] = {}
    initExp_args_dict['args']['n'] = n
    initExp_args_dict['args']['d'] = d
    initExp_args_dict['args']['failure_probability'] = delta
    initExp_args_dict['args']['alg_list'] = alg_list
    initExp_args_dict['args']['participant_to_algorithm_management'] = 'one_to_many' #optional field
    initExp_args_dict['args']['algorithm_management_settings'] = algorithm_management_settings #optional field
    initExp_args_dict['args']['alg_list'] = alg_list #optional field
    initExp_args_dict['app_id'] = app_id

    initExp_args_dict['args']['instructions'] = 'There are instructions'
    initExp_args_dict['args']['debrief'] = 'This is a debrief'

    return initExp_args_dict

if __name__ == "__main__":
    # the dictionary we're checking
    d = PoolBasedTripletMDS_dict()

    # ground truth; this dictionary is assumed to be right
    with open("../PoolBasedTripletMDS.yaml") as f:
        ref = yaml.load(f.read())

    d= {'initExp':d}

    filled, success, message = verify(d, ref)

    if(not success):
        print("\n".join([m['name'] + ": "+m['message'] for m in message]))
