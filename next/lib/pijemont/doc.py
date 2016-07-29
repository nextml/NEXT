import json, sys, yaml, verifier

def get_docs(filename,base_path):
    api,errs = verifier.load_doc(filename,base_path)

    if len(errs) > 0:
        raise Exception("Failed to verify: {}".format(errs))
    
    return api,blank_gen(api),doc_gen(api)

# def print_docs(api_url):
#     api = json.loads(urllib2.urlopen(api_url).read())['api']
#     print(doc_gen(api))

def blank_gen(api):
    return {}

def doc_gen(api):
    return "\n\n".join(["### `{func}({shortargs}) : {shortrets}`\n\n{desc}\n\n#### Arguments:\n{longargs}\n\n#### Returns:\n{longrets}".format(
        func=f,
        shortargs=", ".join(["" + k for k in (api[f]['args'] if 'args' in api[f] else {})]),
        shortrets=args_summary(api[f]['rets']) if 'rets' in api[f] else "None",
        desc = api[f]['description'] if 'description' in api[f] else "",
        longargs = "".join(["\n* `" + k + "` = " + args_gen(api[f]['args'][k],1) for k in (api[f]['args'] if 'args' in api[f] else {})]),
        longrets = args_gen(api[f]['rets'],1) if 'rets' in api[f] else "None"
    ) for f in api])

def args_summary(api):
    if(api["type"] == "list"):
        return "[{}]".format(args_summary(api["values"]))
    elif(api["type"] == "dict"):
        return "{{{}}}".format(", ".join(["{}: {}".format(k, args_summary(api["values"][k])) for k in api["values"]]))
    elif(api["type"] == "tuple"):
        return ", ".join([args_summary(api["values"][k]) for k in api["values"]])
    else:
        return api["type"]

def args_gen(api, depth):
    indent = "   "*depth
    if(api["type"] == "list"):
        return "List, all of whose elements are as follows:  \n{indent}  * {elements}\n".format(indent=indent, elements=args_gen(api['values'], depth+2))
    elif(api["type"] == "dict"):
        return "Dictionary with the following keys:\n{keys}\n{indent}".format(
            indent=indent,
            keys="\n".join(["{indent}`{key}`:{value}  {desc}".format(indent=indent + "* ",
                                                                    key=k,
                                                                    value=args_gen(api['values'][k], depth+1),
                                                                    desc=("\n    "+indent+api['values'][k]['description'] if 'description' in api['values'][k] else ""))
                                                                    for k in api['values']]))
                                
    elif(api["type"] == "tuple"):
        return "Tuple with the following values:\n{values}\n{indent}".format(
            indent=indent,
            keys="\n".join(["{indent}`{key}`:{value}  {desc}".format(indent=indent + "* ",
                                                                    key=str(k),
                                                                    value=args_gen(api['values'][k], depth+1),
                                                                    desc=("\n    "+indent+api['values'][k]['description'] if 'description' in api['values'][k] else ""))
                                                                    for k in api['values']]))
    elif(api["type"] in {"str","string","multiline"}):
        if("values" in api and len(api['values'])>0):
            return "`"+" | ".join(["\"" + k + "\"" for k in api["values"]])+"`"
        else:
            return "`string`{}".format(", "+api["description"] if "description" in api else "")

    elif(api["type"] in {"num","number"}):
        if("values" in api and len(api['values'])>0):
            return "`"+" | ".join([str(k) for k in api["values"]])+"`"
        else:
            return "`num`{}".format(", "+api["description"] if "description" in api else "")
    elif(api["type"] == "file"):
        return "`file`"
    elif(api["type"] == "oneof"):
        return " | ".join([args_gen(api['values'][k], depth+1) for k in api["values"]])
    else:
        return "`{type}`".format(type=api["type"])

