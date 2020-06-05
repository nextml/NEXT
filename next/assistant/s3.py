from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto3
import next.utils as utils
from pprint import pprint
import next.utils as utils
import pandas as pd
import io
from io import BytesIO
import os

os.environ['AWS_SECRET_ACCESS_KEY'] = "0tILCg/PU508Qj9xcgXEkMHVaYUzX3BLkfWEJYOC"
os.environ['AWS_ACCESS_KEY_ID'] = "AKIAI7QXIZD3UTLRBA4Q"
os.environ['AWS_DEFAULT_REGION'] = "us-west-2"
os.environ['AWS_BUCKET_NAME'] = "887f0e0f0bc3cdf0489ea9fd90e263"


def get_decode(label):
    # Dict for encoding
    label = int(label)
    sample_dict = {0:"cell_line", 1:"in_vitro_differentiated_cells", 2:"induced_pluripotent_stem_cells",
                   3:"primary_cells", 4:"stem_cells", 5:"tissue"}
    return sample_dict.get(label)

def df2bytes(df):
    with BytesIO() as f:
        df.to_pickle(f)
        df_bytes = f.getvalue()
    return df_bytes

def create_bucket(AWS_BUCKET_NAME, AWS_ID, AWS_KEY):
    """
    Creates a bucket for an S3 account
    """
    conn = S3Connection(AWS_ID, AWS_KEY)
    bucket = conn.create_bucket(AWS_BUCKET_NAME)
    return bucket


def get_bucket(AWS_BUCKET_NAME, AWS_ID, AWS_KEY):
    """
    Creates a bucket for an S3 account
    """
    conn = S3Connection(AWS_ID, AWS_KEY)
    bucket = conn.get_bucket(AWS_BUCKET_NAME, validate=False)
    return bucket

def upload(filename, file_object, bucket):
    k = Key(bucket)
    k.key = filename
    k.set_contents_from_file(file_object)
    k.set_acl('public-read')
    return k.generate_url(expires_in=0, query_auth=False, force_http=True)


def modify_csv_contents(bucket_name,file_name,labelled_items,batch_no):
    client = boto3.client('s3')
    #obj = client.get_object(Bucket=bucket_id, Key=file_name)
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    obj = client.get_object(Bucket=bucket_name ,Key = file_name)
    file_object= obj["Body"].read()
    label_df = pd.read_csv(io.BytesIO(file_object))

    for index, label in labelled_items:
        label_df.loc[index, 'label'] = get_decode(label)
        label_df.loc[index, 'dataset_type'] = 'train'
        label_df.loc[index, 'batch_no'] = batch_no

    client.put_object(Bucket=bucket_name, Key=file_name, Body=label_df.to_csv(index=False))
    return True

def get_csv_contents(client,bucket_name,file_name):

    # obj = client.get_object(Bucket=bucket_id, Key=file_name)

    obj = client.get_object(Bucket=bucket_name, Key=file_name)
    file_object = obj["Body"].read()
    return file_object


def get_csv_content_dict(bucket_name,file_name_list):
    content_list = {}
    client = boto3.client('s3')
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    for file_name in file_name_list:
        content_list[file_name] = get_csv_contents(client,bucket_name,file_name)

    return content_list


