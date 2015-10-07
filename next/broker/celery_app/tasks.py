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

	def acquire_lock(key,max_rejections=0,time_to_live=0):
		# if acquire_lock is called on a key that has not yet been locked, then returns True
		# if max_rejections>0 then after acquire lock is returned False at least max_rejections times, the lock is unlocked. That is, if max_rejections=4 and acquire_lock is called over and over, then one should expect True,False,False,False,True,False,False,False. However it is possible that the number of False's could be larger than max_rejections due to a race condition.  
		# if time_to_live>0 then the lock is removed after time_to_live seconds after it is First placed.
		lock_name = 'lock:'+str(key)
		lock_count = r.incr(lock_name)

		if lock_count==1:
			if time_to_live>0:
				r.expire(lock_name,time_to_live)
			return True
		else:
			if max_rejections>0 and lock_count>max_rejections:
				r.delete(lock_name)
			return False

	def release_lock(key):
		# Return value: If 0, no prior lock existed. If >0 then removed any existing lock
		lock_name = 'lock:'+str(key)
		return r.delete(lock_name)

	if acquire_lock(namespace,time_to_live=time_limit) and acquire_lock(job_uid,time_to_live=time_limit):

		try:

			print '>>>>>>>> Starting namespace:%s,  time_enqueued=%s <<<<<<<<<' % (namespace,time_enqueued)

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


			# don't forget to release the lock on exp_uid but do not release lock on job_uid because we need to make sure its never touched again
			release_lock(namespace)

			print '########## Finished namespace:%s,  time_enqueued=%s,  execution_time=%s ##########' % (namespace,time_enqueued,dt)

			return return_value
		except:
			te = time.time()
			print '########## TIME EXCEEDED namespace:%s,  time_enqueued=%s,  execution_time=%s, args=%s ##########' % (namespace,time_enqueued,te-ts,str(args))
			# don't forget to release the lock on exp_uid but do not release lock on job_uid because we need to make sure its never touched again
			release_lock(namespace)

			error = traceback.format_exc()
			log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','error':error,'timestamp':next.utils.datetimeNow() } 
			ell.log( app_id+':APP-EXCEPTION', log_entry  )
			return None
		