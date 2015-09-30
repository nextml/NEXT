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
import os
import re
import imp
import sys
import json
import getopt
import zipfile
import requests
import datetime
from StringIO import StringIO

from boto.s3.connection import S3Connection
from boto.s3.key import Key

def generate_target_blob(AWS_BUCKET_NAME,
                         AWS_ID,
                         AWS_KEY,
                         prefix,
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
        AWS_BUCKET_NAME: Aws bucket name
        AWS_ID: Aws id
        AWS_KEY: Aws key
    '''
    targets = []
    bucket = get_AWS_bucket(AWS_BUCKET_NAME, AWS_ID, AWS_KEY)
    print primary_file, primary_type, alt_file, alt_type
    if primary_file.endswith('.zip'):
        target_file_dict, target_name_dict = zipfile_to_dictionary(primary_file)
        if alt_type != 'text':
            assert alt_file != None, 'Need an alt_file.'
            alt_file_dict, alt_name_dict = zipfile_to_dictionary(alt_file)
            try:
                pairs = [(target_name_dict[key],
                          target_file_dict[key],
                          alt_name_dict[key],
                          alt_file_dict[key])
                         for key in target_file_dict.keys()]
            except:
                raise Exception('Primary target names must'
                                'match alt target names.')

            for primary_name, primary_file, alt_name, alt_file in pairs:    
                primary_url = upload_to_S3(bucket,
                                           '{}_{}'.format(prefix,
                                                          primary_name),
                                           StringIO(primary_file))
                alt_url = upload_to_S3(bucket,
                                       '{}_{}'.format(prefix,
                                                      alt_name),
                                       StringIO(alt_file))

                target = {'target_id': '{}_{}'.format(prefix, primary_name),
                          'primary_type': primary_type,
                          'primary_description': primary_url,
                          'alt_type': alt_type,
                          'alt_description': alt_url}
                targets.append(target)
        else:
            if alt_type == 'text':
                for key, primary_file in target_file_dict.iteritems():    
                    primary_file_name = target_name_dict[key]
                    primary_url = upload_to_S3(bucket,
                                               '{}_{}'.format(prefix,
                                                              primary_file_name),
                                               StringIO(primary_file))
                    target = {'target_id': '{}_{}'.format(prefix, primary_file_name),
                              'primary_type': primary_type,
                              'primary_description': primary_url,
                              'alt_type': 'text',
                              'alt_description': primary_file_name}
                    targets.append(target)
                
    elif file.endswith('.txt'):
         with open(file) as f:
            i = 0
            for line in f:
                line = line.strip()
                if line:
                    i += 1
                    target = {'target_id': str(i),
                              'primary_type': 'text',
                              'primary_description':line,
                              'alt_type': 'text',
                              'alt_description':line}
                    targets.append(target)
    else:
        raise Exception('Target file name must be .txt or .zip.')
    return {'target_blob' : targets}

def get_AWS_bucket(AWS_BUCKET_NAME,AWS_ID, AWS_KEY):
    """
    Creates a bucket for an S3 account 
    """
    conn = S3Connection(AWS_ID, AWS_KEY)
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
      target_blob = generate_target_blob(AWS_BUCKET_NAME=AWS_BUCKET_NAME,
                                         AWS_ID=AWS_ID, 
                                         AWS_KEY=AWS_KEY,
                                         prefix=str(datetime.date.today()),
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


