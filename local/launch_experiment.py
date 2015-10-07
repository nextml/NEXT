"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez
last updated: 06/03/2015

A module that can be used to create and launch experiments. Can be imported as a module or used on the command line.

Usage:
As a module:
exp_uid_list, exp_key_list, widget_key_list = launch_experiment(host, experiment_file)

Command line:
python launch_experiment --experiment_file= --next_host=
"""
import os
import re
import csv
import imp
import sys
import json
import getopt
import zipfile
import requests
import datetime
from StringIO import StringIO

def generate_target_blob(prefix,
                         primary_file,                         
                         primary_type,
                         alt_file=None,
                         alt_type='text'):
    '''
    Upload targets and return a target blob for upload with the target_manager.
    
    Inputs: ::\n
        file: fully qualified path of a file on the system. 
	      Must be a zipfile with pictures or a text file.
        prefix: string to prefix every uploaded file name with
    '''
    print "generating blob"
    targets = []
    with open(primary_file, 'r') as manifest_file:
        content = manifest_file.read()
    manifest_dict = json.loads(content)
    
    for key, primary_url in manifest_dict.iteritems():    
        primary_file_name = key
        
        target = {'target_id': '{}_{}'.format(prefix, primary_file_name),
                  'primary_type': primary_type,
                  'primary_description': primary_url,
                  'alt_type': 'text',
                  'alt_description': primary_file_name}
        targets.append(target)
    return {'target_blob' : targets}

def zipfile_to_dictionary(filename): 
    """
    Takes in a zip file and returns a dictionary with the filenames
    as keys and file objects as values

    Inputs: ::\n 
        file: the concerned zip file
        
    Outputs: ::\n
        result: the returned dictionary
    """
    zf = zipfile.ZipFile(filename,'r')
    files_list = zf.namelist() 
    dictionary = {}
    names_dictionary = {}
    for i in files_list:
        if re.search(r"\.(jpe?g|png|gif|bmp|mp4|mp3)",
                     i, re.IGNORECASE):
            f = zf.read(i)
            name = os.path.basename(i).split('.')[0]
            dictionary[name] = f
            names_dictionary[name] = os.path.basename(i)
    return dictionary, names_dictionary

def import_experiment_list(file):
    # Load experiment file
    mod = imp.load_source('experiment', file)
    experiment_list = mod.experiment_list
    return experiment_list

def launch_experiment(host, experiment_list):
  """
  Initialize experiment from an array in an experiment file.
  
  Inputs: ::\n
  	host: hostname of server running next_frontend_base
  	experiment_file: Fully qualified system name of file containing experiment info. Should contain an array called experiment_list, whose elements are dictionaries containing all the info needed to launch an experiment. The dictionary must contain the key initExp, a qualified experiment initialization dictionary. It can also contain an optional target_file key that should be the fully qualified name of a target_file on the system. The target_file can be either text (must end in .txt) or a zipfile containing images (which must end in .zip). Can also add additional context_type and context keys. If the context_type is an image, the context must be a fully qualified file name.
  """  
  exp_uid_list = []
  exp_key_list = []
  widget_key_list = []

  # Initialize experiment
  for experiment in experiment_list:
    # Upload the context if there is one.
    # This is a bit sloppy. Try to think of a better way to do this.
    if 'context' in experiment.keys() and experiment['context_type']=='image':
      print experiment['context'].split("/")[-1], experiment['context'] 
      experiment['initExp']['args']['context'] = context_url
      experiment['initExp']['args']['context_type'] = "image"
    elif 'context' in experiment.keys() and experiment['context_type']=='video':
      print experiment['context'].split("/")[-1], experiment['context'] 
      experiment['initExp']['args']['context'] = context_url
      experiment['initExp']['args']['context_type'] = "video"    
    elif 'context' in experiment.keys():
      experiment['initExp']['args']['context'] = experiment['context']
      experiment['initExp']['args']['context_type'] = experiment['context_type']

    url = 'http://{}/api/experiment'.format(host)  
    print 'Initializing experiment', experiment['initExp']
    response = requests.post(url, json.dumps(experiment['initExp']), headers={'content-type':'application/json'})
    
    initExp_response_dict = json.loads(response.text)
    exp_uid = initExp_response_dict['exp_uid']
    exp_key = initExp_response_dict['exp_key']
    perm_key = initExp_response_dict['perm_key']
    
    exp_uid_list.append(str(exp_uid))
    exp_key_list.append(str(exp_key))
    widget_key_list.append(str(perm_key))
     
    # Upload targets
    if 'primary_target_file' in experiment.keys():
      target_blob = generate_target_blob(prefix=str(datetime.date.today()),
                                         primary_file=experiment['primary_target_file'],
                                         primary_type=experiment['primary_type'],
                                         alt_file=experiment.get('alt_target_file', None),
                                         alt_type=experiment.get('alt_type','text'))
      create_target_mapping_dict = {}
      create_target_mapping_dict['app_id'] = experiment['initExp']['app_id']
      create_target_mapping_dict['exp_uid'] = exp_uid
      create_target_mapping_dict['exp_key'] = exp_key
      create_target_mapping_dict['target_blob'] = target_blob['target_blob']
    
      #print create_target_mapping_dict
      url = 'http://{}/api/targets/createtargetmapping'.format(host)
      response = requests.post(url, json.dumps(create_target_mapping_dict), headers={'content-type':'application/json'})  

    print 'Create Target Mapping response', response, response.text, response.status_code

    print
    print "Query Url is at:", "http://"+host+"/query/query_page/query_page/"+exp_uid+"/"+perm_key
    print

  print "exp_uid_list:", exp_uid_list
  print "exp_key_list:", exp_key_list
  print "widget_key_list:", widget_key_list

  return exp_uid_list, exp_key_list, widget_key_list

if __name__=='__main__':
  opts, args = getopt.getopt(sys.argv[1:], None, ["experiment_file=","next_host="])
  opts = dict(opts)
  print "Mapping targets from ", opts['--experiment_file'], "to", opts['--next_host']
  experiment_list =  import_experiment_list(opts['--experiment_file'])

  #launch_experiment(opts['--next_host'], experiment_list)

