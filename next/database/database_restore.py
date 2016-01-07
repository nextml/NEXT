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
import next.database.database_lib as db_lib
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
filename = 'mongo_dump.tar.gz'
k.get_contents_to_filename(filename)

db_lib.restore_mongodump(filename)
subprocess.call('rm '+filename,shell=True)




	
