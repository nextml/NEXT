#!/usr/bin/python
"""
Restores from from an existing file on S3. 

Example::\n
python daemon_database_restore.py mongo_dump_next-test1.discovery.wisc.edu_2015-04-21_04:50:38.tar.gz

"""

import sys
sys.path.append("/next_backend")

import subprocess
import next.constants as constants
import os

AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']

try:
	dump_filename = sys.argv[1]
except:
	"Must provide a filename from the 'next-database-backups' bucket.\n    python daemon_database_restore.py mongo_dump_next-test1.discovery.wisc.edu_2015-04-21_04:50:38.tar.gz"

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto
# boto.set_stream_logger('boto')

conn = S3Connection(constants.AWS_ACCESS_ID,constants.AWS_SECRET_ACCESS_KEY)
b = conn.get_bucket(AWS_BUCKET_NAME)

k = Key(b)
k.key = dump_filename #'mongo_dump_next-test1.discovery.wisc.edu_2015-04-21_04:50:38.tar.gz'
k.get_contents_to_filename('mongo_dump.tar.gz')

subprocess.call('tar -xvf mongo_dump.tar.gz',shell=True)

subprocess.call('/usr/bin/mongorestore --host {hostname} --port {port} dump/mongo_dump'.format( hostname=constants.MONGODB_HOST, port=constants.MONGODB_PORT ),shell=True)

subprocess.call('rm mongo_dump.tar.gz',shell=True)

subprocess.call('rm -rf dump/mongo_dump',shell=True)





	
