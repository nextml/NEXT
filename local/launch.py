"""
Usage:
    launch.py <init_filename>
    launch.py <init_filename> <targets_path>

Arguments:
    initExp_path (required) : path to a YAML file for arguments to launch experiment
    targets_path (optional) : yaml file that contains the targets information

Options:
    -h, --help

Example:

    > cd ~/Developer/NEXT/local/
    > python launch.py strange_fruit_triplet/init.yaml strange_fruit_triplet/targets.yaml

"""

import os
import sys
from collections import OrderedDict
import base64
import yaml
import requests

sys.path.append('../next/lib')
from docopt import docopt


def get_backend():
    """
    Get the backend host and port.

    Defaults to dict(host='localhost', port=8000).
    """
    return {
        'host': os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost'),
        'port': os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')
    }

def launch(init_filename, targets_filename=None):
    with open(init_filename, 'r') as f:
        init = yaml.load(f)

    if targets_filename:
        with open(targets_filename, 'r') as f:
            targets = yaml.load(f)
            if 'targets' not in init['args']:
                init['args'] = {'targetset': {}}
            if 'targetset' not in init['args']['targets']:
                init['args']['targets']['targetset'] = dict()
            init['args']['targets']['targetset'] = targets

    header = "data:application/{};base64,"
    exp_args = base64.encodestring(yaml.dump(init))
    d = {'args': header.format('x-yaml') + exp_args}

    d = OrderedDict(d)


    header = ['{}:{}'.format(key, len(item)) for key, item in d.items()]
    header = ';'.join(header) + '\n'

    to_send = ''.join([item for _, item in d.items()])

    data = header + to_send
    # -- send the packed experiment definition file
    host = get_backend()
    host_url = "http://{host}:{port}".format(**host)

    r = requests.post(host_url + '/assistant/init/experiment', data=data)
    response = r.json()
    if not response['success']:
        print('An error occurred launching the experiment')
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
    launch(args['<init_filename>'], targets_filename=args['<targets_path>'])
