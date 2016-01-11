"""
Info.py

author: Kevin Jamieson
edited: 11/13/15

This file is used a resource the provides information like a description of this app, the
supported algorithms and default parameters. This is NOT somewhere to retrieve experiment-specific information.
"""
import next.apps.InfoPrototype as InfoPrototype
def get_about():
    """
    Returns description of app
    """
    about_str = (
        """Standard multi-armed bandit problem""")
    return about_str

def get_info_object():
    info = InfoPrototype.get_info_object(get_implemented_algs)
    args =  info['values']['initExp']['values']['args']['values']
    
    args['R'] = {'description': 'Possible rewards from [1..R].',
                 'type':'num',
                 'values':[]}
    
    args['failure_probability'] = {'description': 'Failure probability.',
                                   'type':'num',
                                   'values':[]}
    return info


def get_default_instructions():
    instructions_str = "Please select the rating you think is most appropriate."
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
    import os
    full_path = os.path.realpath(__file__)
    return next(os.walk(os.path.dirname(full_path)+'/algs'))[1]


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
        alg_item['params'] = {}
        alg_list.append(alg_item)

    return alg_list
