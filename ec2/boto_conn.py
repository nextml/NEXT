"""
Load some data from disk, do some shit and save to S3
"""

import json
from datetime import datetime
import time
from sys import argv, stdout
import sys
import traceback

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto
import os


def write_multipart_to_s3(local_filename_path,s3_path,verbose=True):
	"""
	local_filename_path: test.txt
	s3_path: <bucket>/<directory1>/test.txt
	"""
	import math
	from filechunkio import FileChunkIO

	AWS_ACCESS_ID = os.environ.get('AWS_ACCESS_ID', '')
	AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

	split_path = s3_path.split('/')
	AWS_BUCKET = split_path.pop(0)
	AWS_FILENAME = '/'.join(split_path)

	if verbose:
		print AWS_ACCESS_ID
		print AWS_SECRET_ACCESS_KEY
		print AWS_BUCKET
		print AWS_FILENAME

	conn = S3Connection(AWS_ACCESS_ID,AWS_SECRET_ACCESS_KEY)
	b = conn.get_bucket(AWS_BUCKET)

	# Get file info
	source_path = local_filename_path
	source_size = os.stat(source_path).st_size

	

	# Use a chunk size of 50 MiB (feel free to change this)
	chunk_size = 52428800
	chunk_count = int(math.ceil(source_size / float(chunk_size)))

	while True:
		try:
			if verbose: print "trying to save " + local_filename_path + "  to " + AWS_FILENAME

			stdout.flush()
			start = time.time()
			def callback( transmitted, size ):
				"Progress callback for set_contents_from_filename"
				elapsed = time.time() - start
				percent = 100.0 * transmitted / size
				kbps = .001 * transmitted / elapsed
				print ( '\r%d bytes transmitted of %d (%.2f%%),'' %.2f KB/sec ' %
						( transmitted, size, percent, kbps ) ),
				stdout.flush()


			mp = b.initiate_multipart_upload(AWS_FILENAME)

			# Send the file parts, using FileChunkIO to create a file-like object
			# that points to a certain byte range within the original file. We
			# set bytes to never exceed the original file size.
			bytes_saved = 0
			for i in range(chunk_count):
			    offset = chunk_size * i
			    bytes = min(chunk_size, source_size - offset)
			    if verbose: print 'uploading part %d/%d, %d bytes' % (i+1,chunk_count,bytes)  
			    with FileChunkIO(source_path, 'r', offset=offset,bytes=bytes) as fp:
			        mp.upload_part_from_file(fp, part_num=i + 1, cb=callback, num_cb=100 )
			    bytes_saved += bytes

			mp.complete_upload()

			break
		except Exception, error:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			full_error = str(traceback.format_exc())+'\n'+str(error)
			print full_error
			traceback.print_tb(exc_traceback)

	if verbose: print "[ %s ] done with backup of file %s to S3...  %d bytes saved" % (str(datetime.now()),local_filename_path,bytes_saved)
	return True


def write_to_s3(local_filename_path,s3_path,verbose=False):
	"""
	local_filename_path: test.txt
	s3_path: <bucket>/<directory1>/test.txt
	"""

	AWS_ACCESS_ID = os.environ.get('AWS_ACCESS_ID', '')
	AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

	split_path = s3_path.split('/')
	AWS_BUCKET = split_path.pop(0)
	AWS_FILENAME = '/'.join(split_path)

	if verbose:
		print AWS_ACCESS_ID
		print AWS_SECRET_ACCESS_KEY
		print AWS_BUCKET
		print AWS_FILENAME

	conn = S3Connection(AWS_ACCESS_ID,AWS_SECRET_ACCESS_KEY)
	b = conn.get_bucket(AWS_BUCKET)

	while True:
		try:
			if verbose: print "trying to save " + local_filename_path + "  to " + AWS_FILENAME

			stdout.flush()
			start = time.time()
			def callback( transmitted, size ):
				"Progress callback for set_contents_from_filename"
				elapsed = time.time() - start
				percent = 100.0 * transmitted / size
				kbps = .001 * transmitted / elapsed
				if verbose: print ( '\r%d bytes transmitted of %d (%.2f%%),'
						' %.2f KB/sec ' %
						( transmitted, size, percent, kbps ) ),
				stdout.flush()


			k = Key(b)
			k.key = AWS_FILENAME
			bytes_saved = k.set_contents_from_filename( local_filename_path , cb=callback, num_cb=100 )
			break
		except Exception, error:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			full_error = str(traceback.format_exc())+'\n'+str(error)
			print full_error
			traceback.print_tb(exc_traceback)

	if verbose: print "[ %s ] done with backup of file %s to S3...  %d bytes saved" % (str(datetime.now()),local_filename_path,bytes_saved)
	return True


def download_from_s3(s3_path,local_path='.',verbose=True):
	"""
	s3_path: '<bucket>/<directory1>/<filename>'
	local_path: '<local_path>'

	Downloads all files in directory of s3_path, including the directory, and puts them at local_path, creates directories if necessary
	"""

	AWS_ACCESS_ID = os.environ.get('AWS_ACCESS_ID', '')
	AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
	split_path = s3_path.split('/')
	AWS_BUCKET = split_path.pop(0)
	AWS_DIRECTORY = '/'.join(split_path)
	if AWS_DIRECTORY =='':
		AWS_DIRECTORY = None
	conn = S3Connection(AWS_ACCESS_ID,AWS_SECRET_ACCESS_KEY)
	b = conn.get_bucket(AWS_BUCKET,validate=False)
	for key in b.list(AWS_DIRECTORY):
		try:
			directory = os.path.dirname(local_path)
			if not os.path.exists(directory):
				os.makedirs(directory)

			stdout.flush()
			start = time.time()
			def callback( transmitted, size ):
				"Progress callback for set_contents_from_filename"
				elapsed = time.time() - start
				percent = 100.0 * transmitted / size
				kbps = .001 * transmitted / elapsed
				if verbose: print ( '\r%d bytes transmitted of %d (%.2f%%),'
						' %.2f KB/sec ' %
						( transmitted, size, percent, kbps ) ),
				stdout.flush()

			res = key.get_contents_to_filename(filename, cb=callback, num_cb=100 )
		except Exception, error:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			full_error = str(traceback.format_exc())+'\n'+str(error)
			print full_error
			traceback.print_tb(exc_traceback)

def list_files(s3_path):
	AWS_ACCESS_ID = os.environ.get('AWS_ACCESS_ID', '')
	AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
	split_path = s3_path.split('/')
	AWS_BUCKET = split_path.pop(0)
	AWS_DIRECTORY = '/'.join(split_path)
	if AWS_DIRECTORY =='':
		AWS_DIRECTORY = None
	conn = S3Connection(AWS_ACCESS_ID,AWS_SECRET_ACCESS_KEY)
	b = conn.get_bucket(AWS_BUCKET,validate=False)
	return [str(k.name) for k in b.list(AWS_DIRECTORY)]

