"""
Info.py

author: Nick Glattard, n.glattard@gmail.com
edited: 4/27/15

This file is used a resource the provides information like a description of this app, the
supported algorithms and default parameters. This is NOT somewhere to retrieve experiment-specific information.
"""

def get_about():
    """
    Returns description of app
    """
    about_str = (
"""Not yet implemented, need information about tuple bandits""")
    return about_str

def get_default_instructions():
    instructions_str = "Please select the item that is most appropriate."
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
    return ['RandomSampling']


def get_default_alg_list():
    """
    If an alg_list is not specified, these are the parameters are the default parameters that 
    govern which algorithms are run and how they are evaluated
    """

    supported_alg_ids = get_implemented_algs()
    alg_list = []
    for alg_id in supported_alg_ids:
        alg_item = {}
        alg_item['proportion'] = 1./len(supported_alg_ids)
        alg_item['alg_id'] = alg_id
        alg_item['alg_label'] = alg_id
        alg_item['test_alg_label'] = alg_id
        alg_item['params'] = {}
        alg_list.append(alg_item)

    return alg_list