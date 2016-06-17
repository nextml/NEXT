import yaml, json
import random
import numpy
from pprint import pprint
import traceback
import sys
import os
import next.utils as utils

def load_doc(filename):
    with open(filename) as f:
        ref = yaml.load(f.read())

        dir, _ = os.path.split(__file__)
        ds = [load_doc(os.path.join(dir, ext)) for ext in ref.pop('extends',[])]
        utils.debug_print("Loaded {}: {}".format(filename,ref))
        for d in ds:
            ref = merge_dict(ref, d)
            utils.debug_print("Reference dict to date: {}".format(ref))
    return ref

def merge_dict(d1,d2,prefer=1):
    for k in d2:
        if k in d1:
            if type(d1[k]) == dict:
                d1[k] = merge_dict(d1[k],d2[k])
            if prefer == 2:
                d1[k] = d2[k]
        else:
            d1[k] = d2[k]
    return d1

def verify(input_dict, reference_dict):
    """
    Returns: modified_input, success, list_of_errors

    where:
    - modified_input is the input populated with default values where applicable
    - success is a boolean true if there were no problems and false otherwise
    - list_of_errors is as in verify_helper
    """
    input_dict, messages = verify_helper("", input_dict, {'type':'dict','values':reference_dict})

    try:
      if len(messages)>0:
        raise Exception("Failed to verify: {}".format(messages))
      else:
        return input_dict
    except Exception, error:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      print "Exception: {} {}".format(error, traceback.format_exc())
      traceback.print_tb(exc_traceback)
      raise Exception(error)

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
                    if 'default' in reference_dict['values'][k]:
                        input_element[k] = reference_dict['values'][k]['default']
                        if reference_dict['values'][k]['type'] in {'num', 'number'}:
                            input_element[k] = float(input_element[k])
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

    elif reference_dict['type'] == 'tuple':
        if not isinstance(input_element, (list,tuple)):
            ans += [{"name":name, "message":"invalid list"}]
        else:
            for i in range(len(input_element)):
                input_element[i],temp_ans = verify_helper(name+'/'+str(i), input_element[i], reference_dict['values'][str(i)])
                ans += temp_ans

    elif reference_dict['type'] in {'bool', 'boolean'}:
        if not isinstance(input_element, (bool)):
            ans += [{"name":name, "message":"invalid boolean"}]
        elif 'values' in reference_dict and not input_element == reference_dict['values']:
            ans += [{"name":name, "message":"argument must be the following: "+reference_dict['values']}]

    elif reference_dict['type'] in {'num', 'number'}:
        if not isinstance(input_element, (int, long, float)):
            ans += [{"name":name, "message":"invalid number"}]
        elif 'values' in reference_dict and not input_element in reference_dict['values']:
            ans += [{"name":name, "message":"argument must be one of the specified numbers: "+", ".join(reference_dict['values'])}]

    elif reference_dict['type'] in {'str', 'string', 'multiline'}:
        if not isinstance(input_element, (str, unicode)):
            ans += [{"name":name, "message":"expected a string, got {}".format(type(input_element))}]
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
            if 'default' in reference_dict:
                input_element = reference_dict['default']
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
