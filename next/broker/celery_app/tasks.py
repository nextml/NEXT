from __future__ import absolute_import
from .celery_broker import app
import sys
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
import next.apps.Butler as Butler
import redis 
r = redis.StrictRedis(host=next.constants.RABBITREDIS_HOSTNAME, port=next.constants.RABBITREDIS_PORT, db=0)
Butler = Butler.Butler
# Main application task
def apply(app_id, exp_uid, task_name, args_in_json, enqueue_timestamp):

	enqueue_datetime = next.utils.str2datetime(enqueue_timestamp)
	dequeue_datetime = next.utils.datetimeNow()
	delta_datetime = dequeue_datetime - enqueue_datetime
	time_enqueued = delta_datetime.seconds + delta_datetime.microseconds/1000000.

	# modify args_in
	if task_name == 'processAnswer':
		args_in_dict = json.loads(args_in_json)
		args_in_dict['args']['timestamp_answer_received'] = enqueue_timestamp
		args_in_json = json.dumps(args_in_dict)

	# get stateless app
	next_app = next.utils.get_app(app_id, exp_uid, db, ell)

	# pass it to a method
	method = getattr(next_app, task_name)
	response,dt = next.utils.timeit(method)(exp_uid, args_in_json)
        args_out_json,didSucceed,message = response
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

def apply_sync_by_namespace(app_id, exp_uid, alg_id, alg_label, task_name, args, targets, namespace, job_uid, enqueue_timestamp, time_limit):	
	enqueue_datetime = next.utils.str2datetime(enqueue_timestamp)
	dequeue_datetime = next.utils.datetimeNow()
	delta_datetime = dequeue_datetime - enqueue_datetime
	time_enqueued = delta_datetime.seconds + delta_datetime.microseconds/1000000.

	try:
		print '>>>>>>>> Starting namespace:%s,  job_uid=%s,  time_enqueued=%s <<<<<<<<<' % (namespace,job_uid,time_enqueued)
                next_alg = next.utils.get_app_alg(app_id, alg_id)
                butler = Butler(app_id, exp_uid, targets, db, ell, alg_label, alg_id)
		response,dt = next.utils.timeit(getattr(next_alg, task_name))(butler, args)
                log_entry_durations = { 'exp_uid':exp_uid,'alg_label':alg_label,'task':'daemonProcess','duration':dt }
                log_entry_durations.update(butler.algorithms.getDurations())
                log_entry_durations['app_duration'] = dt
                log_entry_durations['duration_enqueued'] = time_enqueued
                log_entry_durations['timestamp'] = next.utils.datetimeNow()
                ell.log( app_id+':ALG-DURATION', log_entry_durations)
		print '########## Finished namespace:%s,  job_uid=%s,  time_enqueued=%s,  execution_time=%s ##########' % (namespace,job_uid,time_enqueued,dt)
		return 
	except Exception, error:
		exc_type, exc_value, exc_traceback = sys.exc_info()
                print "tasks Exception: {} {}".format(error, traceback.format_exc())
                traceback.print_tb(exc_traceback)           
 
		# error = traceback.format_exc()
		# log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','error':error,'timestamp':next.utils.datetimeNow() } 
		# ell.log( app_id+':APP-EXCEPTION', log_entry  )
		return None

        # def daemonProcess(self,exp_uid,args_json,db,ell):
        # try:
        #     # try:
        #     #     args_dict = json.loads(args_json)
        #     # except:
        #     #     error = "%s.daemonProcess input args_json is in improper format" % self.app_id
        #     #     return '{}',False,error
        #     # necessary_fields = ['alg_uid','daemon_args']
        #     # for field in necessary_fields:
        #     #     try:
        #     #         args_dict[field]
        #     #     except KeyError:
        #     #         error = "%s.daemonProcess input arguments missing field: %s" % (self.app_id,str(field)) 
        #     #         return '{}',False,error
        #     #alg_daemon_args = args_dict['daemon_args']
        #     #alg_uid = args_dict['alg_uid']
        #     #alg_id,didSucceed,message = db.get(app_id+':algorithms',alg_uid,'alg_id')

        #     # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
        #     #rc = ResourceClient(app_id,exp_uid,alg_uid,db)

        #     # get specific algorithm to make calls to 
        #     #alg = utils.get_app_alg(self.app_id,alg_id)

        #     #didSucceed,dt = utils.timeit(alg.daemonProcess)(resource=rc,daemon_args_dict=alg_daemon_args)
      

        #     daemon_message = {}
        #     args_out = {'args':daemon_message,'meta':meta}
        #     response_json = json.dumps(args_out)

        #     log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','json':response_json,'timestamp':utils.datetimeNow() } 
        #     ell.log( app_id+':APP-RESPONSE', log_entry  )

        #     return response_json,True,''

        # except Exception, err:
        #     error = traceback.format_exc()
        #     log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','error':error,'timestamp':utils.datetimeNow() } 
        #     ell.log( app_id+':APP-EXCEPTION', log_entry  )
        #     return '{}',False,error

# If celery isn't off, celery-wrap the functions so they can be called with apply_async
if next.constants.CELERY_ON:
        apply = app.task(apply)
        apply_sync_by_namespace = app.task(apply_sync_by_namespace)
