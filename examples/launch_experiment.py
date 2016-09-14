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
import csv
import imp
import sys
import json
import getopt
import zipfile
import requests
import datetime
import time
from StringIO import StringIO
from joblib import Parallel, delayed

from boto.s3.connection import S3Connection
from boto.s3.key import Key


def upload_target_to_S3(target_name_dict, key, bucket, prefix, primary_file,
                        primary_type, extra_target_info={}):
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
    target.update(extra_target_info)
    return target


def generate_target_blob(AWS_BUCKET_NAME,
                         AWS_ID,
                         AWS_KEY,
                         prefix,
                         primary_file,
                         primary_type,
                         experiment=None,
                         alt_file=None,
                         alt_type='text',
                         parallel_upload=True):
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
    print "Uploading targets to S3"
    targets = []
    bucket = get_AWS_bucket(AWS_BUCKET_NAME, AWS_ID, AWS_KEY)
    is_primary_zip = ((type(primary_file) is str and primary_file.endswith('.zip'))
                      or (zipfile.is_zipfile(primary_file)))

    if is_primary_zip:
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
            # This section of the if-statement happens when uploading images
            # from a zip file (e.g., strangefruit30)
            target_features = experiment.get('target_features', None)
            if target_features:
                if type(target_features) != dict:
                    raise ValueError('target_features should be dictionary of '
                                     'form {filename: feature_vector}')
                target_features = {k.replace('.png', '').replace('.jpg', ''): v
                                   for k, v in target_features.items()}
            if type(parallel_upload) == bool and not parallel_upload:
                # happens only for parallel_upload == False
                targets = [upload_target_to_S3(target_name_dict, key, bucket,
                                           prefix, primary_file, primary_type)
                       for i, (key, primary_file) in
                                    enumerate(target_file_dict.iteritems())]
            else:
                # happens only for parallel_upload == True

                if type(parallel_upload) == bool:
                    n_jobs = min(100, len(target_file_dict))
                elif type(parallel_upload) in {int, float}:
                    n_jobs = int(parallel_upload)

                targets = Parallel(n_jobs=n_jobs)(delayed(upload_target_to_S3)
                            (target_name_dict, key, bucket, prefix,
                                primary_file, primary_type,
                                extra_target_info={} if not target_features
                                else {'feature_vector':
                                    target_features[key]})
                           for i, (key, primary_file) in
                                        enumerate(target_file_dict.iteritems()))
    else:
        if experiment.get('image-urls', False) or experiment.get('image-url', False):
            # This is the section where 
            # getting rid of http://filenamestuff?dl=0 to append filenames too
            print('Adding urls to targets')
            targets = []
            urls = open(experiment['primary_target_file'], 'r')
            urls = [url[:-1] for url in urls.readlines()]
            for filename in experiment['initExp']['args']['feature_filenames']:
                # parameters: alt_type, primary_type, prefix
                # define: alt_url, primary_url
                feature_urls = [filename in url for url in urls]
                # assert sum(feature_urls) <= 1, \
                                        # "At most one image URL per filename!"
                if True in feature_urls:
                    url = urls[feature_urls.index(True)]
                    if not '?' in url:
                        url = url + '?dl=1'
                    target = {'target_id': '{}_{}'.format(prefix, filename),
                              'primary_type': primary_type,
                              'primary_description': url,
                              'alt_type': alt_type,
                              'alt_description': filename}

                    targets += [target]
            print('...and done adding URLs to targets')
        else:
            if type(primary_file) is str:
                f = open(primary_file)
            else:
                f = primary_file
                f.seek(0)
            i = 0
            for line in f.read().splitlines():
                line = line.strip()
                if line:
                    i += 1
                    target = {'target_id': str(i),
                              'primary_type': 'text',
                              'primary_description':line,
                              'alt_type': 'text',
                              'alt_description':line}
                    targets.append(target)
        print "\ntargets formatted like \n{}\n".format(targets[0])
    return targets

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
                     i, re.IGNORECASE) and not i.startswith('__MACOSX'):
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

def launch_experiment(host, experiment_list, AWS_ID, AWS_KEY, AWS_BUCKET_NAME,
                      parallel_upload=True):
  """
  Initialize experiment from an array in an experiment file.

  Inputs: ::\n
    host: hostname of server running next_frontend_base
    experiment_file: Fully qualified system name of file containing experiment info. Should contain an array called experiment_list, whose elements are dictionaries containing all the info needed to launch an experiment. The dictionary must contain the key initExp, a qualified experiment initialization dictionary. It can also contain an optional target_file key that should be the fully qualified name of a target_file on the system. The target_file can be either text (must end in .txt) or a zipfile containing images (which must end in .zip). Can also add additional context_type and context keys. If the context_type is an image, the context must be a fully qualified file name.

    AWS_ID: Aws id
    AWS_KEY: Aws key
  """
  exp_uid_list = []
  #exp_key_list = []
  #widget_key_list = []
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

    print 'launch:211', experiment['initExp']['args'].keys()

    # Upload targets
    if 'primary_target_file' in experiment.keys():
        targets = generate_target_blob(AWS_BUCKET_NAME=AWS_BUCKET_NAME,
                                       AWS_ID=AWS_ID,
                                       AWS_KEY=AWS_KEY,
                                       prefix=str(datetime.date.today()),
                                       primary_file=experiment['primary_target_file'],
                                       primary_type=experiment['primary_type'],
                                       alt_file=experiment.get('alt_target_file', None),
                                       experiment=experiment,
                                       alt_type=experiment.get('alt_type','text'),
                                       parallel_upload=parallel_upload)

        experiment['initExp']['args']['targets'] = {'targetset': targets}
    else:
        experiment['initExp']['args']['targets']['n'] = n

    targets = experiment['initExp']['args']['targets']
    n = targets['n'] if 'n' in targets.keys() else len(targets)

    url = 'http://{}/api/experiment'.format(host)
    print 'Initializing experiment', experiment['initExp'].keys()
    response = requests.post(url,
                             json.dumps(experiment['initExp']),
                             headers={'content-type':'application/json'})

    initExp_response_dict = json.loads(response.text)
    print "initExp_response_dict", initExp_response_dict
    exp_uid = initExp_response_dict['exp_uid']
    #exp_key = initExp_response_dict['exp_key']
    #perm_key = initExp_response_dict['perm_key']

    exp_uid_list.append(str(exp_uid))
    #exp_key_list.append(str(exp_key))
    #widget_key_list.append(str(perm_key))

    print "\nQuery Url is at: http://"+host+"/query/query_page/query_page/"+exp_uid + "\n"

  print "exp_uid_list:", exp_uid_list
  #print "exp_key_list:", exp_key_list
  #print "widget_key_list:", widget_key_list

  return exp_uid_list#, exp_key_list, widget_key_list

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
