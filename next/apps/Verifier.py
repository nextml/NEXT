import yaml, json
import random
import numpy
from pprint import pprint

def verify(input_dict, reference_dict):
    """
    Returns: modified_input, success, list_of_errors

    where:
    - modified_input is the input populated with default values where applicable
    - success is a boolean true if there were no problems and false otherwise
    - list_of_errors is as in verify_helper
    """
    
    input_dict, ans = verify_helper("", input_dict, {'type':'dict','values':reference_dict})
    
    # Any further custom verification goes below this line, which may
    # modify input_dict as needed and add any errors to ans as dicts
    # with the format: {"name":problem_key, "message":"what is wrong"}

  # ref_initExp = reference_dict['initExp']['values']
  # ref_args = ref_initExp['args']['values']
  # implemented_algs = ref_args['alg_list']['values']['alg_id']['values']

  # input_args = input_dict['args']
  # input_alg_ids = [d['alg_id'] for d in input_dict['args']['alg_list']]
  # input_alg_labels = [d['alg_label'] for d in input_dict['args']['alg_list']]

  # algorithm_settings = input_dict['args']['algorithm_management_settings']['params']['proportions']

  # for alg_label, alg_id in zip(input_alg_labels, input_alg_ids):

  #     # checking if algorithm is implemented
  #     if alg_id not in implemented_algs:
  #         ans += [{'name': 'initExp/args/alg_list', 'message':'An algorithm ({}) is not implemented'.format(alg_id)}]

  #     # checking to make sure all algorithms in alg_list have settings defined
  #     proportion_algorithms = [alg['alg_label'] for alg in algorithm_settings]
  #     if alg_label not in proportion_algorithms:
  #         ans += [{'name':'initExp/args/algorithm_management_settings',
  #                  'message':('An algorithm in alg_list ({})'
  #                             'is not in in algorithm_management_settings '
  #                             '(in the apprpriate place)').format(algorithm)}]

  # # checking to make sure that the total proportions add up to 1
  # total_proportion = sum(alg['proportion'] for alg in algorithm_settings)
  # if not numpy.allclose(total_proportion, 1):
  #     ans += [{'name':'initExp/args/algorithm_management_settings',
  #             'message':('The algorithm proportions must add up to 1 '
  #                 '(the currently add up to {})'.format(total_proportion))}]

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
        if not isinstance(input_element, (dict)):
            ans += [{"name":name, "message":"invalid dict"}]
        else:
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
                        input_element[k], temp_ans = verify_helper(name + '/' + k, input_element[k], reference_dict['values'][str(k)])
                        ans += temp_ans

    elif reference_dict['type'] == 'list':
        if not isinstance(input_element, (list)):
            ans += [{"name":name, "message":"invalid list"}]
        else:
            for i in range(len(input_element)):
                input_element[i],temp_ans = verify_helper(name+'/'+str(i), input_element[i], reference_dict['values'])
                ans += temp_ans

    elif reference_dict['type'] == 'num':
        if not isinstance(input_element, (int, long, float)):
            ans += [{"name":name, "message":"invalid number"}]

    elif reference_dict['type'] == 'str' or reference_dict['type'] == 'multiline':
        if not isinstance(input_element, (str, unicode)):
            ans += [{"name":name, "message":"invalid string"}]
        elif 'values' in reference_dict and not input_element in reference_dict['values']:
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
    return [k for k in d1 if not k in d2], [k for k in d2 if not k in d1]


if __name__ == "__main__":
    # the dictionary we're checking
    #d = json.loads('./Apps/PoolBasedTripletMDS/PoolBasedTripletMDS.yaml')
    d = {'app_id': 'PoolBasedTripletMDS',
            'args': {'targets':{'n': 30}, 'alg_list': [{'alg_id': 'RandomSampling',
                        'alg_label': 'Test',
                        'test_alg_label': 'Test'},
                       {'alg_id': 'RandomSampling',
                        'alg_label': 'Random',
                        'test_alg_label': 'Test'},
                       {'alg_id': 'UncertaintySampling',
                        'alg_label': 'Uncertainty Sampling',
                        'test_alg_label': 'Test'},
                       {'alg_id': 'CrowdKernel',
                        'alg_label': 'Crowd Kernel',
                        'test_alg_label': 'Test'}],
          'algorithm_management_settings': {'mode': 'fixed_proportions',
                                            'params': [{'alg_label': 'Test',
                                                        'proportion': 0.2},
                                                       {'alg_label': 'Random',
                                                        'proportion': 0.26666666666666666},
                                                       {'alg_label': 'Uncertainty Sampling',
                                                        'proportion': 0.26666666666666666},
                                                       {'alg_label': 'Crowd Kernel',
                                                        'proportion': 0.26666666666666666}]},
            'd': 2,
            'failure_probability': 0.01,
            'participant_to_algorithm_management': 'one_to_many'},
          }

    # ground truth; this dictionary is assumed to be right
    filename = "Apps/PoolBasedTripletMDS/PoolBasedTripletMDS.yaml"
    with open(filename) as f:
        ref = yaml.load(f.read())

    d= {'initExp':d}

    filled, success, message = verify(d['initExp'], ref['initExp']['values'])

    print("\n".join([m['name'] + ": "+m['message'] for m in message]))
