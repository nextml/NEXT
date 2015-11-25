from __future__ import absolute_import
from .celery_broker import app
import time
import json
import traceback

# import next.logging_client.LoggerHTTP as ell
from next.database_client.DatabaseAPI import DatabaseAPI
db = DatabaseAPI()
from next.logging_client.LoggerAPI import LoggerAPI
ell = LoggerAPI()

import next.utils
import next.constants

import redis 
r = redis.StrictRedis(host=next.constants.RABBITREDIS_HOSTNAME, port=next.constants.RABBITREDIS_PORT, db=0)

# Main application task
@app.task
def apply(app_id, exp_uid, task_name, args_in_json, enqueue_timestamp):

	enqueue_datetime = next.utils.str2datetime(enqueue_timestamp)
	dequeue_datetime = next.utils.datetimeNow()
	delta_datetime = dequeue_datetime - enqueue_datetime
	time_enqueued = delta_datetime.seconds + delta_datetime.microseconds/1000000.

	# modify args_in
	if task_name == 'processAnswer':
		args_in_dict = json.loads(args_in_json)
		args_in_dict['meta'] = {'timestamp_answer_received':enqueue_timestamp}
		args_in_json = json.dumps(args_in_dict)

	# get stateless app
	next_app = next.utils.get_app(app_id)

	# pass it to a method
	method = getattr(next_app, task_name)
	args_out_json,didSucceed,message,dt = next.utils.timeit(method)(exp_uid, args_in_json, db, ell)
	args_out_dict = json.loads(args_out_json)
	if 'args' in args_out_dict:
		return_value = (json.dumps(args_out_dict['args']),didSucceed,message)
		meta = args_out_dict.get('meta',{})

		if 'log_entry_durations' in meta:
			log_entry_durations = meta['log_entry_durations']
			log_entry_durations['app_duration'] = dt
			log_entry_durations['duration_enqueued'] = time_enqueued
			log_entry_durations['timestamp'] = next.utils.datetimeNow()
			ell.log( app_id+':ALG-DURATION', log_entry_durations  )
	else:
		return_value = (args_out_json,didSucceed,message)


	print '#### Finished %s,  time_enqueued=%s,  execution_time=%s ####' % (task_name,time_enqueued,dt)

	return return_value


@app.task
def apply_sync_by_namespace(app_id, exp_uid, task_name, args, namespace, job_uid, enqueue_timestamp, time_limit):
	
	enqueue_datetime = next.utils.str2datetime(enqueue_timestamp)
	dequeue_datetime = next.utils.datetimeNow()
	delta_datetime = dequeue_datetime - enqueue_datetime
	time_enqueued = delta_datetime.seconds + delta_datetime.microseconds/1000000.

	try:

		print '>>>>>>>> Starting namespace:%s,  job_uid=%s,  time_enqueued=%s <<<<<<<<<' % (namespace,job_uid,time_enqueued)

		# get stateless app
		next_app = next.utils.get_app(app_id)

		# pass it to a method
		method = getattr(next_app, task_name)
		ts = time.time()
		args_out_json,didSucceed,message,dt = next.utils.timeit(method)(exp_uid, args, db, ell)
		args_out_dict = json.loads(args_out_json)
		if 'args' in args_out_dict:
			return_value = (json.dumps(args_out_dict['args']),didSucceed,message)
			meta = args_out_dict.get('meta',{})

			if 'log_entry_durations' in meta:
				log_entry_durations = meta['log_entry_durations']
				log_entry_durations['app_duration'] = dt
				log_entry_durations['duration_enqueued'] = time_enqueued
				log_entry_durations['timestamp'] = next.utils.datetimeNow()
				ell.log( app_id+':ALG-DURATION', log_entry_durations  )
		else:
			return_value = (args_out_json,didSucceed,message)

		print '########## Finished namespace:%s,  job_uid=%s,  time_enqueued=%s,  execution_time=%s ##########' % (namespace,job_uid,time_enqueued,dt)

		return return_value
	except:
		
		error = traceback.format_exc()
		log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','error':error,'timestamp':next.utils.datetimeNow() } 
		ell.log( app_id+':APP-EXCEPTION', log_entry  )
		return None

		