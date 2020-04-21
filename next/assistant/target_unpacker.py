import zipfile
import io
import os
from joblib import Parallel, delayed
from StringIO import StringIO
import base64
import random
import sys
import json
import pandas as pd
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
                    'mp4': 'video', 'mov': 'video',
                    'txt': 'text', 'csv': 'text'}
    filetype = filename.split('.')[-1]
    if filetype not in target_types:
        msg = ('Target not recognized (extension: "{}"). '
               'Available extensions: {}').format(filetype, list(target_types.keys()))
        raise ValueError(msg)

    utils.debug_print('Done uploading target: {}'.format(filename))

    return {'target_id': str(i),
            'primary_type': target_types[filetype],
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
    filenames = zip_file.namelist()
    filenames = [f for f in filenames if not any([ignore in f.lower() for ignore in
                                                  ['ds_store', 'icon', '__macosx']])]
    filenames = [f for f in filenames if len(f.split('/')[-1]) > 0]
    filenames = sorted(filenames)
    items_file = zip_file.open(filenames[0])
    # items_file.readable = lambda: True
    # items_file.writable = lambda: False
    # items_file.seekable = lambda: False
    # items_file.read1 = items_file.read
    items_file = io.TextIOWrapper(items_file)
    file_df = pd.read_csv(items_file)
    # files is has at least one key; (tested before call in assistant_blueprint.py)

    if kind in {'csv', 'txt'}:

        targets = []
        label_map = dict(cell_line=0, in_vitro_differentiated_cells=1,induced_pluripotent_stem_cells=2,primary_cells=3,
                         stem_cells=4,tissue=5)

        for i, row in file_df.iterrows():

            targets.append({'target_id': str(i),

                        'primary_type': 'text',
                        'primary_description': row.loc['key_value'],
                        'alt_type': 'text',
                        'alt_description': row.loc['ontology_mapping'],
                        'meta':
                            {'features': [],
                              'label': label_map.get(row.loc['label'],'NaN')
                             }
                        })

        return targets
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
