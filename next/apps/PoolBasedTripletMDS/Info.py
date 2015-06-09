"""
Info.py

author: Kevin Jamieson (kevin.g.jamieson@gmail.com)
edited: 2/17/15

This file is used a resource the provides information like a description of this app, the
supported algorithms and default parameters. This is NOT somewhere to retrieve experiment-specific information.
"""

def get_about():
    """
    Returns description of app
    """
    about_str = (
"""PoolBasedTripletMDS applies crowd-sourcing and adaptive sampling to 
non-metric multidimensional scaling (NMDS). The NMDS objective is simple enough to state. 
Condsider n objects (e.g. different kinds of beer) and suppose you are given a set of relations 
like "object A is more similar to object B than C." For a large set of these relations and given a 
desired dimension input, NMDS attempts to find a set of n points in d-dimensions, denoted 
x1,x2,...,xn where each xi is a d-dimensional vector, that best agrees with the given relations in 
the sense that if "object A is more similar to object B than C" then NMDS tries to find a set of points 
in which ||xA - xB||_2 < ||xA - xC||_2 on as many of these triplets as possible (Note, ||z||_2 is 
defined as the 2-norm: ||z||_2 = sqrt( z(1)^2 + z(2)^2 + ... + z(n)^2 )). The set of points, or 
embedding, is evaluated on different metrics, the most natural one being the number of relations, or triplets 
the embedding fails to satisfy in the given set of relations.""")
    return about_str

def get_default_instructions():
    instructions_str = "Please select, using your mouse or left and right arrow keys, the item on the bottom that is closest to the top."
    return instructions_str

def get_default_debrief():
    debrief = "Thank you for participating"
    return debrief_str

def get_default_num_tries():
    num_tries = 100
    return num_tries

def get_implemented_algs():
    """
    Returns list of algorithms that are fully operational and implemented for this app
    """
    return ['UncertaintySampling','RandomSampling','CrowdKernel','STE']


def get_default_alg_list():
    """
    If an alg_list is not specified, these are the parameters are the default parameters that 
    govern which algorithms are run and how they are evaluated
    """

    supported_alg_ids = get_implemented_algs()
    if 'RandomSampling' not in supported_alg_ids:
        raise
    elif 'UncertaintySampling' not in supported_alg_ids:
        raise
    elif 'CrowdKernel' not in supported_alg_ids:
        raise
    elif 'STE' not in supported_alg_ids:
        raise

    alg_list = []

    test_proportion = 0.1
    test_alg = {}
    test_alg['proportion'] = test_proportion
    test_alg['alg_id'] = 'RandomSampling'
    test_alg['alg_label'] = 'Test'
    test_alg['test_alg_label'] = 'Test'
    test_alg['params'] = {}
    alg_list.append(test_alg)

    num_candidate_algs = 2.

    random_alg = {}
    random_alg['proportion'] = (1. - test_proportion)/num_candidate_algs
    random_alg['alg_id'] = 'RandomSampling'
    random_alg['alg_label'] = 'Random'
    random_alg['test_alg_label'] = 'Test'
    random_alg['params'] = {}
    alg_list.append(random_alg)

    uncertainty_sampling_alg = {}
    uncertainty_sampling_alg['proportion'] = (1. - test_proportion)/num_candidate_algs
    uncertainty_sampling_alg['alg_id'] = 'UncertaintySampling'
    uncertainty_sampling_alg['alg_label'] = 'Uncertainty Sampling'
    uncertainty_sampling_alg['test_alg_label'] = 'Test'
    uncertainty_sampling_alg['params'] = {}
    alg_list.append(uncertainty_sampling_alg)

    crowd_kernel_alg = {}
    crowd_kernel_alg['proportion'] = (1. - test_proportion)/num_candidate_algs
    crowd_kernel_alg['alg_id'] = 'CrowdKernel'
    crowd_kernel_alg['alg_label'] = 'CrowdKernel'
    crowd_kernel_alg['test_alg_label'] = 'Test'
    crowd_kernel_alg['params'] = {}
    alg_list.append(crowd_kernel_alg)

    ste_alg = {}
    ste_alg['proportion'] = (1. - test_proportion)/num_candidate_algs
    ste_alg['alg_id'] = 'STE'
    ste_alg['alg_label'] = 'STE'
    ste_alg['test_alg_label'] = 'Test'
    ste_alg['params'] = {}
    alg_list.append(ste_alg)


    
    return alg_list
