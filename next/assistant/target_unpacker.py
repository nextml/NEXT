import zipfile
import io
import os
from joblib import Parallel, delayed
from StringIO import StringIO
import random
import sys

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

    files = {}
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
    url = s3.upload(filename,  StringIO(file_obj), bucket)
    target_types = {'png': 'image', 'jpeg': 'image', 'jpg': 'image',
                    'mp4': 'movie', 'mov': 'movie',
                    'txt': 'text'}

    return {'target_id': str(i),
            'primary_type': target_types[filename.split('.')[-1]],
            'primary_description': url,
            'alt_type': 'text',
            'alt_description': filename}

def unpack(s, aws_key, aws_secret_key, n_jobs=20, bucket_name=None):
    s = base64.decodestring(s)
    base64_zip = io.BytesIO(s)
    zip_file = zipfile.ZipFile(base64_zip)
    files = zipfile_to_dictionary(zip_file)

    # TODO: trim here for JSON object to append to dictionaries
    # TODO: manage CSV targets here
    # TODO: how come creating a S3 bucket isn't working for me?
    if not bucket_name:
        bucket_name = '{}{}'.format(aws_key.lower(), utils.random_string(length=20))
    targets = Parallel(n_jobs=n_jobs)(delayed(upload_target)
                          (name, file, bucket_name, aws_key, aws_secret_key,
                           i=i, get_bucket=True)
               for i, (name, file) in enumerate(files.items()))
    return targets

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
