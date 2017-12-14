import zipfile
import io
import os
from joblib import Parallel, delayed
from StringIO import StringIO
import base64
import random
import sys
import json
from collections import OrderedDict

if __name__ == "__main__":
    sys.path.append('../..')

import next.utils as utils
import next.assistant.s3 as s3


def zipfile_to_dictionary(zip_file):
    """
    Takes in a zip file and returns a dictionary with the filenames
    as keys and file objects as values

    Inputs: ::\n
        file: the concerned zip file

    Outputs: ::\n
        result: the returned dictionary
    """
    filenames = zip_file.namelist()
    filenames = [f for f in filenames if not any([ignore in f.lower() for ignore in
                                             ['ds_store', 'icon', '__macosx']])]
    filenames = [f for f in filenames if len(f.split('/')[-1]) > 0]
    filenames = sorted(filenames)

    files = OrderedDict()
    for filename in filenames:
        f = zip_file.read(filename)
        name = filename.split('/')[-1]
        files[name] = f
    return files

def upload_target(filename, file_obj, bucket_name, aws_key, aws_secret_key,
                  i=None, get_bucket=True):
    if get_bucket:
        bucket = s3.get_bucket(bucket_name, aws_key, aws_secret_key)
    else:
        bucket = s3.create_bucket(bucket_name, aws_key, aws_secret_key)

    utils.debug_print('Uploading target: {}'.format(filename))
    url = s3.upload(filename,  StringIO(file_obj), bucket)
    target_types = {'png': 'image', 'jpeg': 'image', 'jpg': 'image', 'gif': 'image',
                    'mp4': 'movie', 'mov': 'movie',
                    'txt': 'text', 'csv': 'text'}
    utils.debug_print('Done uploading target: {}'.format(filename))

    return {'target_id': str(i),
            'primary_type': target_types[filename.split('.')[-1]],
            'primary_description': url,
            'alt_type': 'text',
            'alt_description': filename}

def get_filenames_from_zip(s):
    base64_zip = io.BytesIO(s)
    zip_file = zipfile.ZipFile(base64_zip)
    return zip_file.namelist()


def unpack(s, aws_key, aws_secret_key, bucket_name, n_jobs=None,
           get_bucket=True):
    base64_zip = io.BytesIO(s)
    zip_file = zipfile.ZipFile(base64_zip)
    files = zipfile_to_dictionary(zip_file)

    if not n_jobs:
        n_jobs = min(len(files), 50)

    if not bucket_name:
        bucket_name = '{}{}'.format(aws_key.lower(), utils.random_string(length=20))

    # TODO: trim here for JSON object to append to dictionaries
    # TODO: manage CSV targets here
    # TODO: how come creating a S3 bucket isn't working for me?
    utils.debug_print('=== Starting upload of targets to S3 ===')
    try:
        targets = Parallel(n_jobs=n_jobs, backend='threading') \
                    (delayed(upload_target, check_pickle=False)
                              (name, file, bucket_name, aws_key, aws_secret_key,
                               i=i, get_bucket=True)
                   for i, (name, file) in enumerate(files.items()))
    except:
        utils.debug_print('Whoops, parallel S3 upload failed. Trying serially.')
        targets = [upload_target(name, file, bucket_name, aws_key, aws_secret_key,
                                 i=i, get_bucket=True)
                   for i, (name, file) in enumerate(files.items())]
    return targets


def unpack_text_file(s, kind='csv'):
    kind = kind.lower()  # always lower case extension
    base64_zip = io.BytesIO(s)
    zip_file = zipfile.ZipFile(base64_zip)
    files = zipfile_to_dictionary(zip_file)

    # files is has at least one key; (tested before call in assistant_blueprint.py)
    file_str = files[files.keys()[0]]
    if kind in {'csv', 'txt'}:
        strings = file_str.split('\n')  # -1 because last newline
        strings = list(filter(lambda x: len(x) > 0, strings))
        targets = [{'target_id': str(i),
                    'primary_type': 'text',
                    'primary_description': string,
                    'alt_type': 'text',
                    'alt_description': string}
                   for i, string in enumerate(strings)]
        return targets
    elif kind in {'json'}:
        return json.loads(file_str)
    else:
        raise ValueError('`kind` not regonized in `unpack_text_file`')


if __name__ == "__main__":
    from pprint import pprint
    aws_key = os.environ.get('KEY')
    aws_secret_access_key = os.environ.get('ACCESS_KEY')

    with open('../../examples/strange_fruit_triplet/strangefruit30.zip', 'rb') as f:
        s = f.read()
    print(s)
    targets = unpack(s, aws_key, aws_secret_access_key,
                     bucket_name='scott_test')
    pprint(targets)
