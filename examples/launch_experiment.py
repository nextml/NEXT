"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez
last updated: 06/03/2015

A module that can be used to create and launch experiments. Can be imported as a module or used on the command line.

Usage:
As a module:
exp_uid_list, exp_key_list, widget_key_list = launch_experiment(host, experiment_file, AWS_ID, AWS_KEY)

Command line:
export NEXT_FRONTEND_GLOBAL_HOST=
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
python launch_experiment --experiment_file=
"""
import random
import json
import time, datetime
import requests
import os, sys, getopt, imp
import csv, zipfile, getopt
from StringIO import StringIO
from boto.s3.connection import S3Connection
from boto.s3.key import Key

def generate_target_blob(file, prefix, AWS_BUCKET_NAME, AWS_ID, AWS_KEY):
    """
    Upload targets and return a target blob for upload with the target_manager.
    
    Inputs: ::\n
        file: fully qualified path of a file on the system. Must be a zipfile with pictures or a text file.
        prefix: string to prefix every uploaded file name with
        AWS_BUCKET_NAME: Aws bucket name
        AWS_ID: Aws id
        AWS_KEY: Aws key
    """
    targets = []
    if file.endswith('.zip'):
        target_file_dict = zipfile_to_dictionary(file)
        bucket = get_AWS_bucket(AWS_BUCKET_NAME, AWS_ID, AWS_KEY)        
        for target_name in target_file_dict.keys():
            print "uploading", target_name
            target_file = target_file_dict[target_name]
            target_url = upload_to_S3(bucket, prefix+"_"+target_name, StringIO(target_file))
            print "success", target_url
            if target_name.endswith(('jpg','png')):
                primary_type = 'image'
            elif target_name.endswith('mp4'):
                primary_type = 'video'
            else:
                primary_type = 'other'
            print "primary_type", primary_type
            target = {  'target_id': prefix+"_"+target_name,
                        'primary_type': primary_type,
                        'primary_description': target_url,
                        'alt_type': 'text',
                        'alt_description': target_name
                     }
            targets.append(target)

    elif file.endswith('.txt'):
         i = 0
         with open(file) as f:
            for line in f:
                line = line.strip()
                if line:
                    i += 1
                    target = {  'target_id': str(i),
                                'primary_type': 'text',
                                'primary_description':line,
                                'alt_type': 'text',
                                'alt_description':line
                                }
                    targets.append(target)
    else:
        raise Exception('Target file name must be .txt or .zip.')

    # print targets
    return {'target_blob' : targets}

def get_AWS_bucket(AWS_BUCKET_NAME,AWS_ID, AWS_KEY):
    """
    Creates a bucket for an S3 account 

    """
    conn = S3Connection(AWS_ID, AWS_KEY)
    #Maybe by default we should try to create bucket and then catch exception?
    #Also, migrate the bucket name to settings.Config
    bucket = conn.get_bucket(AWS_BUCKET_NAME)
    return bucket            

def upload_to_S3(bucket, key, file_object):
    """
    Uploads a file object to a S3 instance

    Inputs: ::\n 
        bucket: S3 bucket we want to upload to
        key: the key to access the file in the bucket;
        file_object: the file that needs to be uploaded

    """   
    k = Key(bucket)
    k.key = key
    k.set_contents_from_file(file_object)
    k.set_acl('public-read')
    return k.generate_url(expires_in=0, query_auth=False, force_http=True)

def zipfile_to_dictionary(filename): 
    """
    Takes in a zip file and returns a dictionary with the filenames
    as keys and file objects as values

    Inputs: ::\n 
        file: the concerned zip file
        
    Outputs: ::\n
        result: the returned dictionary
    """
    listOfFiles= []
    dictionary ={}
    print "filename in z to d",filename 
    zf = zipfile.ZipFile(filename,'r')
    listOfFiles = zf.namelist() 
    for i in listOfFiles:
        if not i.startswith('__MACOSX') and i.endswith(('jpg','jpeg','png','gif','bmp', 'mp4')):
            f= zf.read(i)
            dictionary[i] = f
        
    return dictionary

def import_experiment_list(file):
    # Load experiment file
    mod=imp.load_source('experiment', experiment_file)
    experiment_list = mod.experiment_list
    return experiment_list

def launch_experiment(host, experiment_list, AWS_ID, AWS_KEY, AWS_BUCKET_NAME):
  """
  Initialize experiment from an array in an experiment file.
  
  Inputs: ::\n
  	host: hostname of server running next_frontend_base
  	experiment_file: Fully qualified system name of file containing experiment info. Should contain an array called experiment_list, whose elements are dictionaries containing all the info needed to launch an experiment. The dictionary must contain the key initExp, a qualified experiment initialization dictionary. It can also contain an optional target_file key that should be the fully qualified name of a target_file on the system. The target_file can be either text (must end in .txt) or a zipfile containing images (which must end in .zip). Can also add additional context_type and context keys. If the context_type is an image, the context must be a fully qualified file name.

  	AWS_ID: Aws id
  	AWS_KEY: Aws key
  """  
  exp_uid_list = []
  exp_key_list = []
  widget_key_list = []

  # establish S3 connection and use boto get_bucket
  bucket = get_AWS_bucket(AWS_BUCKET_NAME, AWS_ID, AWS_KEY)

  # Initialize experiment
  for experiment in experiment_list:
    # Upload the context if there is one.
    # This is a bit sloppy. Try to think of a better way to do this.
    if 'context' in experiment.keys() and experiment['context_type']=='image':
      print experiment['context'].split("/")[-1], experiment['context'] 
      context_url = upload_to_S3(bucket, experiment['context'].split("/")[-1], open(experiment['context']))
      experiment['initExp']['args']['context'] = context_url
      experiment['initExp']['args']['context_type'] = "image"
    elif 'context' in experiment.keys() and experiment['context_type']=='video':
      print experiment['context'].split("/")[-1], experiment['context'] 
      context_url = upload_to_S3(bucket, experiment['context'].split("/")[-1], open(experiment['context']))
      experiment['initExp']['args']['context'] = context_url
      experiment['initExp']['args']['context_type'] = "video"    
    elif 'context' in experiment.keys():
      experiment['initExp']['args']['context'] = experiment['context']
      experiment['initExp']['args']['context_type'] = experiment['context_type']

    url = "http://"+host+"/api/experiment"  
    print "Initializing experiment", experiment['initExp']
    response = requests.post(url, json.dumps(experiment['initExp']), headers={'content-type':'application/json'})
    print "initExp response = ",response.text, response.status_code
    
    initExp_response_dict = json.loads(response.text)
    exp_uid = initExp_response_dict['exp_uid']
    exp_key = initExp_response_dict['exp_key']
    perm_key = initExp_response_dict['perm_key']
    
    exp_uid_list.append(str(exp_uid))
    exp_key_list.append(str(exp_key))
    widget_key_list.append(str(perm_key))
     
    # Upload targets
    if 'target_file' in experiment.keys():
      target_file = experiment['target_file'] 
      print "target file in launch_Experiment", target_file
      target_blob = generate_target_blob(file=target_file,
                                         prefix=str(datetime.date.today()),
                                         AWS_BUCKET_NAME=AWS_BUCKET_NAME,
                                         AWS_ID=AWS_ID, 
                                         AWS_KEY=AWS_KEY)
      create_target_mapping_dict = {}
      create_target_mapping_dict['app_id'] = experiment['initExp']['app_id']
      create_target_mapping_dict['exp_uid'] = exp_uid
      create_target_mapping_dict['exp_key'] = exp_key
      create_target_mapping_dict['target_blob'] = target_blob['target_blob']
    
      #print create_target_mapping_dict
      url = "http://"+host+"/api/targets/createtargetmapping"
      response = requests.post(url, json.dumps(create_target_mapping_dict), headers={'content-type':'application/json'})  

    print "Create Target Mapping response", response, response.text, response.status_code

    print
    print "Query Url is at:", "http://"+host+"/query/query_page/query_page/"+exp_uid+"/"+perm_key
    print

  print "exp_uid_list:", exp_uid_list
  print "exp_key_list:", exp_key_list
  print "widget_key_list:", widget_key_list

  return exp_uid_list, exp_key_list, widget_key_list

if __name__=='__main__':
  opts, args = getopt.getopt(sys.argv[1:], None, ["experiment_file="])
  opts = dict(opts) 
  # Make sure to check for aws id and key here
  if not 'AWS_SECRET_ACCESS_KEY' in os.environ.keys() or not 'AWS_ACCESS_KEY_ID' in os.environ.keys() or not 'NEXT_BACKEND_GLOBAL_HOST' or not 'AWS_BUCKET_NAME' in os.environ.keys():
    print "You must set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, NEXT_BACKEND_GLOBAL_HOST, AWS_BUCKET_NAME as environment variables"
    sys.exit()
  print opts['--experiment_file']
  port = os.environ.keys.get('NEXT_BACKEND_GLOBAL_PORT',8000)
  experiment_list =  import_experiment_list(opts['--experiment_file'])

  launch_experiment(os.environ.get('NEXT_BACKEND_GLOBAL_HOST')+":"+port, experiment_list, AWS_ID=os.environ.get('AWS_ACCESS_KEY_ID'), AWS_KEY=os.environ.get('AWS_SECRET_ACCESS_KEY'), AWS_BUCKET_NAME=os.environ.get('AWS_BUCKET_NAME') )

#if __name__ == "__main__":
#    opts, args = getopt.getopt(sys.argv[1:], None, ["prefix=","file=","bucket=", "AWS_ID=", "AWS_KEY="])
#    opts = dict(opts)
#    print generate_target_blob(opts['--file'], opts['--prefix'], opts['--bucket'], opts['--id'], opts['--key'])


