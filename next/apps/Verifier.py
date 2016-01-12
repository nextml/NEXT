import yaml, json

def verify(input_dict, reference_dict):
    """
    Returns: modified_input, success, list_of_errors

    where: 
    - modified_input is the input populated with default values where applicable
    - success is a boolean true if there were no problems and false otherwise
    - list_of_errors is as in verify_helper
    """
    ans = []
    for k in reference_dict:
        input_dict, temp_ans = verify_helper(k, input_dict[k], reference_dict[k])
        ans += temp_ans

    # Any further custom verification goes below this line, which may
    # modify input_dict as needed and add any errors to ans as dicts
    # with the format: {"name":problem_key, "message":"what is wrong"}
    
    return input_dict, len(ans) == 0, ans
    
def verify_helper(name, input_element, reference_dict):
    """
    Returns: modified_input,list_of_errors

    where list of errors is: [{name: name, message: ...}, ...]
    """
    ans = []
    if reference_dict['type'] == 'dict':
        l1,l2 = compare_dict_keys(input_element, reference_dict['values'])
        if len(l1) > 0:
            ans += [{"name":name, "message":"extra keys in input: " + ",".join(l1)}]
        else:
            ok = True
            for k in l2:
                if 'default' in reference_dict['values'][k]:
                    input_element[k] = reference_dict['values'][k]['default']
                elif not 'required' in reference_dict['values'][k] or reference_dict['values'][k]['required'] == False:
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
        if isinstance(input_element, (int, long, float)):
            ans += [{"name":name, "message":"invalid number"}]

    elif reference_dict['type'] == 'str':
        if isinstance(input_element, str):
            ans += [{"name":name, "message":"invalid string"}]

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


# with open("old_dictionary.py") as f:
#     d = json.loads(f.read())
    
# with open("PoolBasedTripletMDS.yaml") as f:
#     ref = yaml.load(f.read())

# d= {'initExp':d}
    
# filled, success, message = verify(d, ref)
# if(not success):
#     print("\n".join([m['name'] + ": "+m['message'] for m in message]))
