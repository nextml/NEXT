"""
Can be run with

    cd /path/to/pijemont
    py.test

The following command will print sys.stdout

    py.test -s

"""
from __future__ import print_function

import json, sys, yaml, os
from pprint import pprint
import pytest
from .. import verifier

def verify_yaml(test_name, test):
    """
    This function does the actual work of verifying the YAML. It reads the spec
    in, formats the args (loaded from test_files/{test_name}) then returns both
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    api, errs = verifier.load_doc(test['spec'], os.path.join(dir_path,'specs/'))
    if len(errs) > 0:
        return None, None, errs
    fn = test['inputs'][test_name]['function']
    args = test['inputs'][test_name]['args']
    verified = verifier.verify(args, api[fn]['args'])
    expected_out = test['inputs'][test_name]['verified']
    return verified, expected_out, None


def run_test(filename):
    """
    Given a filename, this function runs the test specified in that file.

    It catches Exceptions raised and prints out each test it's doing.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dir_path,'test_files/{}'.format(filename))) as f:
        test = yaml.load(f.read())
    for test_name in test['inputs']:
        print('    {}'.format(test_name))
        if test['load_errors']:
            args, out, load_errs = verify_yaml(test_name, test)
            assert (not load_errs is None) and len(load_errs) > 0
        else:
            try:
                args, expected_out, load_errs = verify_yaml(test_name, test)
                assert expected_out == args
                assert (not 'errors' in test['inputs'][test_name]) or test['inputs'][test_name]['errors'] == False
            except:
                assert 'errors' in test['inputs'][test_name] and test['inputs'][test_name]['errors'] == True


def test_all():
    """
    Loop over all the files in tests/test_files and run all of them.
    """
    print('\n')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_ = os.path.join(dir_path,'test_files/')
    for yaml_filename in os.listdir(dir_):
        if 'DS_Store' in yaml_filename:
            continue
        print('Testing YAML file {}'.format(yaml_filename))
        run_test(yaml_filename)

if __name__ == "__main__":
    test_all()
