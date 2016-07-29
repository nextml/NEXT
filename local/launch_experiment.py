"""
author: Lalit Jain, lalitkumarjj@gmail.com
modified: Chris Fernandez
last updated: 06/03/2015

A module that can be used to create and launch experiments. Can be imported as a module or used on the command line.

Usage:
As a module:
exp_uid_list, exp_key_list, widget_key_list = launch_experiment(host, experiment_file)

Command line:
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
from StringIO import StringIO

def generate_target_blob(prefix,
                         primary_file,
                         primary_type,
                         experiment=None,
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
                    target = {'target_id': '{}_{}'.format(prefix, primary_name),
                          'primary_type': primary_type,
                          'alt_type': alt_type,
                          'alt_description': alt_url}
                    targets.append(target)
        else:
           for i, (key, primary_file) in enumerate(target_file_dict.iteritems()):
                primary_file_name = target_name_dict[key]
                if i % 100 == 0 and i != 0:
                    print('percent done = {}'.format(i / 50e3))
                target = {'target_id': '{}_{}'.format(prefix, primary_file_name),
                          'primary_type': primary_type,
                          'alt_type': 'text',
                          'alt_description': primary_file_name}
                targets.append(target)
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

def launch_experiment(host, experiment_list):
  """
  Initialize experiment from an array in an experiment file.

  Inputs: ::\n
    host: hostname of server running next_frontend_base
    experiment_file: Fully qualified system name of file containing experiment info. Should contain an array called experiment_list, whose elements are dictionaries containing all the info needed to launch an experiment. The dictionary must contain the key initExp, a qualified experiment initialization dictionary. It can also contain an optional target_file key that should be the fully qualified name of a target_file on the system. The target_file can be either text (must end in .txt) or a zipfile containing images (which must end in .zip). Can also add additional context_type and context keys. If the context_type is an image, the context must be a fully qualified file name.
  """
  exp_uid_list = []
  #exp_key_list = []
  #widget_key_list = []
  # establish S3 connection and use boto get_bucket

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

    print 'launch:211', experiment['initExp']['args'].keys()

    # Upload targets
    if 'primary_target_file' in experiment.keys():
        targets = generate_target_blob(prefix=str(datetime.date.today()),
                                       primary_file=experiment['primary_target_file'],
                                       primary_type=experiment['primary_type'],
                                       alt_file=experiment.get('alt_target_file', None),
                                       experiment=experiment,
                                       alt_type=experiment.get('alt_type','text'))

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
  print "Mapping targets from ", opts['--experiment_file'], "to", opts['--next_host']
  experiment_list = import_experiment_list(opts['--experiment_file'])

  launch_experiment(opts['--next_host'], experiment_list)
