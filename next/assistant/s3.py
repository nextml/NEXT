from boto.s3.connection import S3Connection
from boto.s3.key import Key
import next.utils as utils
from pprint import pprint


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
