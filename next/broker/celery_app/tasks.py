from __future__ import absolute_import
from .celery_broker import app
import celery.signals
import os
import sys
import time
import json
import traceback
import numpy
from next.constants import DEBUG_ON

# import next.logging_client.LoggerHTTP as ell
from next.database_client.DatabaseAPI import DatabaseAPI
db = DatabaseAPI()
from next.logging_client.LoggerAPI import LoggerAPI
ell = LoggerAPI()
import next.utils
import next.constants
import next.apps.Butler as Butler
import next.apps.Verifier as Verifier

Butler = Butler.Butler

class App_Wrapper:
        def __init__(self, app_id, exp_uid, db, ell):
                self.next_app = next.utils.get_app(app_id, exp_uid, db, ell)
                self.butler = Butler(app_id, exp_uid, app.myApp.TargetManager, db, ell)

        def get_model(self, args_in_json):
                next_app = utils.get_app(app_id, exp_uid, self.db, self.ell)
                response, dt = next.utils.timeit(next_app.getModel)(exp_uid, args_in_json)
                args_out_json,didSucceed,message = response
                args_out_dict = json.loads(args_out_json)
                meta = args_out_dict.get('meta',{})
                if 'log_entry_durations' in meta:
                        log_entry_durations = meta['log_entry_durations']
                        log_entry_durations['app_duration'] = dt
                        log_entry_durations['duration_enqueued'] = 0.
                        log_entry_durations['timestamp'] = utils.datetimeNow()
                        butler.ell.log( app_id+':ALG-DURATION', log_entry_durations  )
                self.log_entry_durations = log_entry_durations
                self.app_dt = dt
                return args_out_dict['args']
                
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

def apply_dashboard(app_id, exp_uid, args_in_json, enqueue_timestamp):
	enqueue_datetime = next.utils.str2datetime(enqueue_timestamp)
	dequeue_datetime = next.utils.datetimeNow()
	delta_datetime = dequeue_datetime - enqueue_datetime
	time_enqueued = delta_datetime.seconds + delta_datetime.microseconds/1000000.
        dir, _ = os.path.split(__file__)
        reference_dict = Verifier.load_doc(os.path.join('next/apps', 'Apps/{}/{}.yaml'.format(app_id, app_id)))
        args_dict = Verifier.verify(args_in_json, reference_dict['getStats']['values'])
        stat_id = args_dict['args'].pop('stat_id',None)

        app = App_Wrapper(app_id, exp_uid, db, ell)
        
        dashboard_string = 'next.apps.Apps.' + app_id + '.dashboard.Dashboard'
        dashboard_module = __import__(dashboard_string, fromlist=[''])
        dashboard = getattr(dashboard_module, app_id+'Dashboard')
        dashboard = dashboard(butler.db, butler.ell)
        stats_method = getattr(dashboard, stat_id)

        response,dt = next.utils.timeit(stats_method)(app,
                                                      butler,
                                                      **args_dict['args']['params'])
        if DEBUG_ON:
            next.utils.debug_print('#### Finished Dashboard %s, time_enqueued=%s,  execution_time=%s ####' % (stat_id, time_enqueued, dt), color='white')
	return json.dumps(response), True, ''


def apply_sync_by_namespace(app_id, exp_uid, alg_id, alg_label, task_name, args, namespace, job_uid, enqueue_timestamp, time_limit):	
	enqueue_datetime = next.utils.str2datetime(enqueue_timestamp)
	dequeue_datetime = next.utils.datetimeNow()
	delta_datetime = dequeue_datetime - enqueue_datetime
	time_enqueued = delta_datetime.seconds + delta_datetime.microseconds/1000000.

	try:
		print '>>>>>>>> Starting namespace:%s,  job_uid=%s,  time_enqueued=%s <<<<<<<<<' % (namespace,job_uid,time_enqueued)
                # get stateless app
                next_app = next.utils.get_app(app_id, exp_uid, db, ell)
                target_manager = next_app.myApp.TargetManager
                next_alg = next.utils.get_app_alg(app_id, alg_id)
                butler = Butler(app_id, exp_uid, target_manager, db, ell, alg_label, alg_id)
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

# forces each worker to get its own random seed. 
@celery.signals.worker_process_init.connect()
def seed_rng(**_):
    """
    Seeds the numpy random number generator.
    """
    numpy.random.seed()

# If celery isn't off, celery-wrap the functions so they can be called with apply_async
if next.constants.CELERY_ON:
        apply = app.task(apply)
        apply_dashboard = app.task(apply_dashboard)
        apply_sync_by_namespace = app.task(apply_sync_by_namespace)

