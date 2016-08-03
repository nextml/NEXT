import yaml, json
import random
import traceback
import sys
import os
from .condition import condition_parser

DICT = {'dict','dictionary','map'}
LIST = {'list'}
TUPLE = {'tuple'}
ONEOF = {'oneof'}

NUM = {'num','number','float'}
STRING = {'str','string','multiline'}
ANY = {'any','stuff'}
FILE = {'file'}
BOOL = {'boolean','bool'}

def load_doc(filename,base_path):
    errs = []
    with open(os.path.join(base_path,filename)) as f:
        ref = yaml.load(f.read())
        ds = []
        for ext in ref.pop('extends',[]):
            r,e = load_doc(ext,base_path)
            ds += [r]
            errs += e
        for d in ds:
            ref = merge_dict(ref, d)
    errs = check_format(ref,'args' in ref[list(ref.keys())[0]])
    return ref,errs

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

def check_format(doc,rets=True):
    errs = []
    if rets:
        for x in doc:
            if 'args' in doc[x]:
                errs += check_format_helper({'type':'dict','values':doc[x]['args']},'args/'+x)
            if 'rets' in doc[x]:
                errs += check_format_helper(doc[x]['rets'],'rets/'+x)
    else:
        for x in doc:
            errs += check_format_helper(doc[x],x)
    return errs

def check_format_helper(doc,name):
    errs = []
    
    if not 'type' in doc:
        errs += ['{}: "type" key missing'.format(name)]
    
    diff = set(doc.keys()) - {'type','description','values','optional','default'}
    if len(diff) > 0:
        errs += ["{}: extra keys in spec: {}".format(name,", ".join(list(diff)))]
    
    if not doc['type'] in DICT | LIST | TUPLE | ONEOF | NUM | STRING | BOOL | ANY | FILE:
        errs += ['{}: invlid type: {}'.format(name, doc['type'])]
    
    if doc['type'] in DICT | LIST | TUPLE | ONEOF and not 'values' in doc:
        errs += ['{}: requires "values" key'.format(name)]

    if len(errs) > 0:
        return errs
    
    if doc['type'] in DICT:
        for x in doc['values']:
            errs += check_format_helper(doc['values'][x],'{}/{}'.format(name,x))
    
    elif doc['type'] in LIST:
        errs += check_format_helper(doc['values'],'{}/values'.format(name))
        
    elif doc['type'] in TUPLE:
        for x in doc['values']:
            errs += check_format_helper(doc['values'][x],'{}/{}'.format(name,str(x)))
            
    elif doc['type'] in ONEOF:
        for x in doc['values']:
            errs += check_format_helper(doc['values'][x],'{}/{}'.format(name,str(x)))
            
    return errs
        
    
    

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
    except Exception as error:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      print("Exception: {} {}".format(error, traceback.format_exc()))
      traceback.print_tb(exc_traceback)
      raise Exception(error.args[0])

def verify_helper(name, input_element, reference_dict):
    """
    Returns: modified_input,list_of_errors

    where:

    - modified_input is the input populated with default values
    - list_of_errors is: [{name: name, message: ...}, ...]
    """
    ans = []
    if reference_dict['type'] in DICT:
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
                        if reference_dict['values'][k]['type'] in NUM:
                            input_element[k] = float(input_element[k])
                    elif (not 'optional' in reference_dict['values'][k]) or reference_dict['values'][k]['optional'] == False:
                        ans += [{"name":name+'/'+k, "message":"required key is absent"}]
                        ok = False
                if(ok):
                    for k in input_element:
                        input_element[k], temp_ans = verify_helper(name + '/' + k, input_element[k], reference_dict['values'][str(k)])
                        ans += temp_ans

    elif reference_dict['type'] in LIST:
        if not isinstance(input_element, (list)):
            ans += [{"name":name, "message":"invalid list"}]
        else:
            for i in range(len(input_element)):
                input_element[i],temp_ans = verify_helper(name+'/'+str(i), input_element[i], reference_dict['values'])
                ans += temp_ans

    elif reference_dict['type'] in TUPLE:
        if not isinstance(input_element, (list,tuple)):
            ans += [{"name":name, "message":"invalid tuple"}]
        else:
            new_tuple = list(input_element)
            for i in range(len(input_element)):
                new_tuple[i], temp_ans = verify_helper(name+'/'+str(i), input_element[i], reference_dict['values'][i])
                ans += temp_ans
            new_tuple = tuple(new_tuple)

    elif reference_dict['type'] in BOOL:
        if not isinstance(input_element, (bool)):
            ans += [{"name":name, "message":"invalid boolean"}]

    elif reference_dict['type'] in NUM:
        ok = True
        if not isinstance(input_element, (int, float, long)):
            if isinstance(input_element, (str, unicode)):
                try:
                    input_element = float(input_element)
                except:
                    ans += [{"name":name, "message":"invalid number"}]
                    ok = False
            else:
                ans += [{"name":name, "message":"invalid number"}]
                ok = False
        if ok:
            if 'values' in reference_dict:
                try:
                    condition_parser().parse("{} {}".format(str(input_element),str(reference_dict['values'])))
                except Exception as exc:
                    ans += [{"name":name, "message":str(exc)}]

    elif reference_dict['type'] in STRING:
        if not isinstance(input_element, (str, unicode)):
            ans += [{"name":name, "message":"expected a string, got {}".format(type(input_element))}]
        elif 'values' in reference_dict and not input_element in reference_dict['values']:
            ans += [{"name":name, "message":"argument must be one of the specified strings: "+", ".join(reference_dict['values'])}]

    elif reference_dict['type'] in ONEOF:
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

    elif reference_dict['type'] in ANY | FILE:
        pass

    else:
        ans += [{"name":name, "message":"invalid type: {}".format(reference_dict['type'])}]  

    return input_element,ans

def compare_dict_keys(d1, d2):
    """
    Returns [things in d1 not in d2, things in d2 not in d1]
    """
    return [k for k in d1 if not k in d2], [k for k in d2 if not k in d1]

if __name__ == '__main__':
    if len(sys.argv) > 1:
        r,e = load_doc(sys.argv[1])
        print('doc',r)
        print('errs',e)
        if len(sys.argv) > 2:
            i,e = verify(sys.argv[2],r)
            print("Errors",e)
            print("Verified input",i)
    
