"""
Usage:
    launch.py <init_filename>
    launch.py <init_filename> <zip_path>

Arguments:
    initExp_path (required) : path to a YAML file for arguments to launch experiment
    zip_path (optional)     : zip file that contains the targets
                              (which are then uploaded to S3).

Options:
    -h, --help

Example:

    > cd ~/Developer/NEXT/examples/
    > python launch.py strange_fruit_triplet/init.yaml strange_fruit_triplet/strangefruit30.zip

"""

from __future__ import print_function
import os
import sys
from collections import OrderedDict
import base64
import yaml
import requests

sys.path.append('../../next/lib')
from docopt import docopt


def verify_environ():
    to_have = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_BUCKET_NAME']
    for key in to_have:
        if key not in os.environ:
            print('Must define ' + key)
    if 'NEXT_BACKEND_GLOBAL_HOST' not in os.environ:
        print('NEXT_BACKEND_GLOBAL_HOST is not defined, '
              'defaulting to localhost')


def launch(init_filename, targets_filename=None):
    verify_environ()

    with open(init_filename, 'r') as f:
        init = yaml.load(f)

    header = "data:application/{};base64,"
    args = base64.encodestring(yaml.dump(init))
    d = {'args': header.format('x-yaml') + args,
         'key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
         'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
         'bucket_id': os.environ.get('AWS_BUCKET_NAME')}

    if targets_filename:
        with open(targets_filename, 'r') as f:
            targets = f.read()
        d['targets'] = header.format('zip') + base64.encodestring(targets)

    d = OrderedDict(d)

    host_url = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')
    host_url = 'http://' + host_url + ':8000'

    header = ['{}:{}'.format(key, len(item)) for key, item in d.items()]
    header = ';'.join(header) + '\n'

    to_send = ''.join([item for _, item in d.items()])

    data = header + to_send

    r = requests.post(host_url + '/assistant/init/experiment', data=data)
    response = r.json()
    if not response['success']:
        print('An error occured launching the experiment')
        print(response['message'])
        sys.exit()

    dashboard_url = host_url + '/dashboard/experiment_dashboard/{}/{}'
    dashboard_url = dashboard_url.format(response['exp_uid'], init['app_id'])
    print('Dashboard URL:\n    {}'.format(dashboard_url))
    print('\n')
    print('NEXT Home URL:\n    {}'.format(host_url + '/home'))
    return response

if __name__ == "__main__":
    args = docopt(__doc__)
    print(args)
    print('')
    launch(args['<init_filename>'], targets_filename=args['<zip_path>'])
