#!/usr/bin/python
"""
Every 30 minutes backs up database to S3. To recover the database, (i.e. reverse the process)
simply download the file from S3, un-tar it, and use the command:

(./)mongorestore --host {hostname} --port {port} path/to/dump/mongodump

where {hostname} and {port} are as they are below
"""
import sys
sys.path.append("/next_backend")

import time
import traceback

import next.utils as utils

import subprocess
import next.constants as constants
import os


NEXT_BACKEND_GLOBAL_HOST = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')
AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME','next-database-backups')


timestamp = utils.datetimeNow()
print "[ %s ] starting backup of MongoDB to S3..." % str(timestamp)

print "[ %s ] constants.AWS_ACCESS_ID = %s" % (str(timestamp),constants.AWS_ACCESS_ID)

subprocess.call('/usr/bin/mongodump -vvvvv --host {hostname}:{port} --out /dump/mongo_dump'.format( hostname=constants.MONGODB_HOST, port=constants.MONGODB_PORT ),shell=True)
	
try:
	tar_file = sys.argv[1]
except:
	tar_file = 'mongo_dump_{hostname}_{timestamp}.tar.gz'.format( hostname=NEXT_BACKEND_GLOBAL_HOST, timestamp= timestamp.strftime("%Y-%m-%d_%H:%M:%S") )

subprocess.call('tar czf {path}/{tar_file} /dump/mongo_dump'.format(path='/dump',tar_file=tar_file),shell=True)


from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto
# boto.set_stream_logger('boto')
try:
	conn = S3Connection(constants.AWS_ACCESS_ID,constants.AWS_SECRET_ACCESS_KEY)
	b = conn.get_bucket(AWS_BUCKET_NAME)

	k = Key(b)
	k.key = tar_file
	bytes_saved = k.set_contents_from_filename( '/dump/'+tar_file )

	timestamp = utils.datetimeNow()
	print "[ %s ] done with backup of MongoDB to S3...  %d bytes saved" % (str(timestamp),bytes_saved)
except:
	error = traceback.format_exc()
	timestamp = utils.datetimeNow()
	print "[ %s ] FAILED TO CONNECT TO S3... saving locally" % str(timestamp)
	print error

subprocess.call('rm {path}/{tar_file} /dump/mongo_dump'.format(path='/dump',tar_file=tar_file),shell=True)


	


	
