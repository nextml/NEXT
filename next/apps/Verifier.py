import yaml, json
import random
import numpy

import tests

def verify(input_dict, reference_dict):
    """
    Returns: modified_input, success, list_of_errors

    where:
    - modified_input is the input populated with default values where applicable
    - success is a boolean true if there were no problems and false otherwise
    - list_of_errors is as in verify_helper
    """
    ans = []
    for k in input_dict:
        input_dict, temp_ans = verify_helper(k, input_dict[k], reference_dict[k])
        ans += temp_ans

    # Any further custom verification goes below this line, which may
    # modify input_dict as needed and add any errors to ans as dicts
    # with the format: {"name":problem_key, "message":"what is wrong"}

    ref_initExp = reference_dict['initExp']['values']
    ref_args = ref_initExp['args']['values']
    implemented_algs = ref_args['alg_list']['values']['alg_id']['values']

    input_args = input_dict['args']
    input_alg_ids = [d['alg_id'] for d in input_dict['args']['alg_list']]
    input_alg_labels = [d['alg_label'] for d in input_dict['args']['alg_list']]

    algorithm_settings = input_dict['args']['algorithm_management_settings']['params']['proportions']

    for alg_label, alg_id in zip(input_alg_labels, input_alg_ids):

        # checking if algorithm is implemented
        if alg_id not in implemented_algs:
            ans += [{'name': 'initExp/args/alg_list', 'message':'An algorithm ({}) is not implemented'.format(alg_id)}]

        # checking to make sure all algorithms in alg_list have settings defined
        porportion_algorithms = [alg['alg_label'] for alg in algorithm_settings]
        if alg_label not in porportion_algorithms:
            ans += [{'name':'initExp/args/algorithm_management_settings',
                     'message':('An algorithm in alg_list ({})'
                                'is not in in algorithm_management_settings '
                                '(in the apprpriate place)').format(algorithm)}]

    # checking to make sure that the total porportions add up to 1
    total_porportion = sum(alg['proportion'] for alg in algorithm_settings)
    if not numpy.allclose(total_porportion, 1):
        ans += [{'name':'initExp/args/algorithm_management_settings',
                'message':('The algorithm porportions must add up to 1 '
                    '(the currently add up to {})'.format(total_porportion))}]

    return input_dict, len(ans) == 0, ans

def verify_helper(name, input_element, reference_dict):
    """
    Returns: modified_input,list_of_errors

    where:

    - modified_input is the input populated with default values
    - list_of_errors is: [{name: name, message: ...}, ...]
    """
    ans = []
    if reference_dict['type'] == 'dict':
        l1,l2 = compare_dict_keys(input_element, reference_dict['values'])
        if len(l1) > 0:
            ans += [{"name":name, "message":"extra keys in input: " + ",".join(l1)}]
        else:
            ok = True
            for k in l2:
                if 'set' in reference_dict['values'][k]:
                    input_element[k] = reference_dict['values'][k]['set']
                elif (not 'optional' in reference_dict['values'][k]) or reference_dict['values'][k]['optional'] == False:
                    ans += [{"name":name+'/'+k, "message":"required key is absent"}]
                    ok = False
            if(ok):
                for k in input_element:
                    input_element[k],temp_ans = verify_helper(name + '/' + k, input_element[k],reference_dict['values'][str(k)])
                    ans += temp_ans

    elif reference_dict['type'] == 'list':
        for i in range(len(input_element)):
            input_element[i],temp_ans = verify_helper(name+'/'+str(i), input_element[i], reference_dict['values'])
            ans += temp_ans

    elif reference_dict['type'] == 'num':
        if not isinstance(input_element, (int, long, float)):
            ans += [{"name":name, "message":"invalid number"}]

    elif reference_dict['type'] == 'str' or reference_dict['type'] == 'multiline':
        if not isinstance(input_element, str):
            ans += [{"name":name, "message":"invalid string"}]
        if not input_element in reference_dict['values']:
            ans += [{"name":name, "message":"argument must be one of the specified strings: "+", ".join(reference_dict['values'])}]

    elif reference_dict['type'] == 'oneof':
        count = 0
        for k in reference_dict['values']:
            if k in input_element:
                count += 1
                if count > 1:
                    ans += [{"name":name+"/"+k,"message":"More than one argument specified for 'oneof arg: " + name}]
        if count == 0:
            if 'set' in reference_dict:
                input_element = reference_dict['set']
            else:
                ans += [{"name":name, "message":"no argument provided for 'oneof' arg"}]

    elif reference_dict['type'] == 'target':
        pass
    elif reference_dict['type'] == 'targetset':
        pass
    elif reference_dict['type'] == 'targetmeta':
        pass

    return input_element,ans

def compare_dict_keys(d1, d2):
    """
    Returns [things in d1 not in d2, things in d2 not in d1]
    """
    return [k for k in d1 if not k in d2],[k for k in d2 if not k in d1]


def description(filename):
    """
    Gets descriptions for a particular app.

    :input filename: Filename of a .yaml descriptor of an app. For example,
    `PoolBasedTripletMDS.yaml`.
    :returns: The description, as specified by the YAML file but as a dict.
    """
    with open(filename) as f:
        return yaml.load(f.read())


if __name__ == "__main__":
    # the dictionary we're checking
    d = tests.PoolBasedTripletMDS_dict()

    # ground truth; this dictionary is assumed to be right
    filename = "PoolBasedTripletMDS.yaml"
    with open(filename) as f:
        ref = yaml.load(f.read())

    d= {'initExp':d}

    filled, success, message = verify(d, ref)

    if(not success):
        print("\n".join([m['name'] + ": "+m['message'] for m in message]))
