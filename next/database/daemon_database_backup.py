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

while(1):

	timestamp = utils.datetimeNow()
	print "[ %s ] Calling database daemon..." % str(timestamp)
	subprocess.call('python ./next/database/database_backup.py',shell=True)

	time.sleep(1800)


	

	


	
