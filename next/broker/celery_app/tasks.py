from __future__ import absolute_import
from .celery_broker import app
import celery.signals
import os
import sys
import time
import json
import traceback
import numpy
import hashlib

import next.utils
import next.constants
from next.constants import DEBUG_ON

from next.database_client.DatabaseAPI import DatabaseAPI, DatabaseException
from next.logging_client.LoggerAPI import LoggerAPI

from next.apps.Butler import Butler
import next.lib.pijemont.verifier as verifier

db, ell = None, None

def worker_connect_db():
    next.utils.debug_print("Initializing worker database connection")
    backoff_dt = 0.01
    while True:
        try:
            db, ell = DatabaseAPI(), LoggerAPI()
            break
        except DatabaseException as e:
            next.utils.debug_print("Failed to connect to database ({}), retrying in {}s".format(e, backoff_dt))
            time.sleep(backoff_dt)
            backoff_dt *= 2

            # If we've tried too many times, make the database failure /loud/.
            if backoff_dt > 1:
                raise e

    return db, ell

# if we're not using celery, just initialize the database globally
if next.constants.CELERY_ON:
    db, ell = worker_connect_db()

# runs for each worker process spawned by Celery
# we initialize the DatabaseAPI per worker here
@celery.signals.worker_process_init.connect
def on_connect(**kwargs):
    global db, ell
    # make sure every worker has a different random seed (very important for randomized algorithms)
    numpy.random.seed()

    db, ell = worker_connect_db()

# runs when each Celery worker process shuts down
# we'll close the database connections here
@celery.signals.worker_process_shutdown.connect
def on_shutdown(**kwargs):
    if db:
        next.utils.debug_print("Closing worker's database connections")
        db.close()
    if ell:
        next.utils.debug_print("Closing worker's logger connections")
        ell.close()

class App_Wrapper:
        def __init__(self, app_id, exp_uid, db, ell):
                self.app_id = app_id
                self.exp_uid = exp_uid
                self.next_app = next.utils.get_app(app_id, exp_uid, db, ell)
                self.butler = Butler(app_id, exp_uid, self.next_app.myApp.TargetManager, db, ell)

        def getModel(self, args_in_json):
                response, dt = next.utils.timeit(self.next_app.getModel)(self.next_app.exp_uid, args_in_json)
                args_out_json,didSucceed,message = response
                args_out_dict = json.loads(args_out_json)
                meta = args_out_dict.get('meta',{})
                if 'log_entry_durations' in meta.keys():
                        self.log_entry_durations = meta['log_entry_durations']
                        self.log_entry_durations['timestamp'] = next.utils.datetimeNow()                  
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
	response, dt = next.utils.timeit(method)(exp_uid, args_in_json)
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
        reference_dict,errs = verifier.load_doc('{}/myApp.yaml'.format(app_id, app_id),"apps/")
        if len(errs) > 0:
                raise Exception("App YAML format errors: \n{}".format(str(errs)))
        args_dict = verifier.verify(args_in_json, reference_dict['getStats']['args'])
        stat_id = args_dict['args'].get('stat_id','none')

        stat_args = args_dict['args']

        hash_object = hashlib.md5(stat_id+'_'+json.dumps(stat_args['params']))
        stat_uid = hash_object.hexdigest()
        stat_uid += '_' + exp_uid

        app = App_Wrapper(app_id, exp_uid, db, ell)
        cached_doc = app.butler.dashboard.get(uid=stat_uid)
        cached_response = None
        if (int(stat_args.get('force_recompute',0))==0) and (cached_doc is not None):    
          delta_datetime = (next.utils.datetimeNow() - next.utils.str2datetime(cached_doc['timestamp']))
          if delta_datetime.seconds < next.constants.DASHBOARD_STALENESS_IN_SECONDS:
            cached_response = json.loads(cached_doc['data_dict'])
            if 'meta' not in cached_response:
              cached_response['meta']={}
            cached_response['meta']['cached'] = 1
            if delta_datetime.seconds/60<1:
                cached_response['meta']['last_dashboard_update'] = '<1 minute ago'
            else:
                cached_response['meta']['last_dashboard_update'] = str(delta_datetime.seconds/60)+' minutes ago'

        if cached_response==None:
            dashboard_string = 'apps.' + app_id + '.dashboard.Dashboard'
            dashboard_module = __import__(dashboard_string, fromlist=[''])
            dashboard = getattr(dashboard_module, 'MyAppDashboard')
            dashboard = dashboard(db, ell)
            stats_method = getattr(dashboard, stat_id)
            response,dt = next.utils.timeit(stats_method)(app,app.butler,**args_dict['args']['params'])
            
            save_dict = {'exp_uid':app.exp_uid,
                    'stat_uid':stat_uid,
                    'timestamp':next.utils.datetime2str(next.utils.datetimeNow()),
                    'data_dict':json.dumps(response)}
            app.butler.dashboard.set_many(uid=stat_uid,key_value_dict=save_dict)

            # update the admin timing with the timing of a getModel
            if hasattr(app, 'log_entry_durations'):
                app.log_entry_durations['app_duration'] = dt
                app.log_entry_durations['duration_enqueued'] = time_enqueued
                app.butler.ell.log(app.app_id+':ALG-DURATION', app.log_entry_durations)
        else:
            response = cached_response

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

# If celery isn't off, celery-wrap the functions so they can be called with apply_async
if next.constants.CELERY_ON:
        apply = app.task(apply)
        apply_dashboard = app.task(apply_dashboard)
        apply_sync_by_namespace = app.task(apply_sync_by_namespace)

