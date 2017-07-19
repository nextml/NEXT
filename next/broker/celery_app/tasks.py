from __future__ import absolute_import
import os
import sys
import time
import json
import hashlib
import traceback
from functools import wraps
import numpy
import celery.signals
from .celery_broker import app

import next.utils
import next.constants
import next.lib.pijemont.verifier as verifier
from next.constants import DEBUG_ON
from next.apps.Butler import Butler
from next.database_client.DatabaseAPI import DatabaseAPI
from next.logging_client.LoggerAPI import LoggerAPI

db = DatabaseAPI()
ell = LoggerAPI()


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

def handle_exception(f, app, task_name):
    @wraps(f)
    def wrapper(exp_uid, args_json):
        try:
            return f(exp_uid, args_json)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_error = str(traceback.format_exc())+'\n'+str(e)
            next.utils.debug_print("{} Exception: {}".format(task_name, e), color='red')
            log_entry = {'exp_uid': exp_uid,
                         'task': task_name,
                         'error': full_error,
                         'timestamp': next.utils.datetimeNow(),
                         'args_json': args_json}
            app.butler.ell.log(app.app_id+':APP-EXCEPTION', log_entry)
            traceback.print_tb(exc_traceback)
            return '{}', False, str(e)
    return wrapper

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

    response, dt = next.utils.timeit(handle_exception(method, next_app, task_name))(exp_uid, args_in_json)
    args_out_json, didSucceed, message = response
    args_out_dict = json.loads(args_out_json)

    if 'args' in args_out_dict:
        return_value = (json.dumps(args_out_dict['args']), didSucceed, message)
        meta = args_out_dict.get('meta', {})
        if 'log_entry_durations' in meta:
            log_entry_durations = meta['log_entry_durations']
            log_entry_durations['app_duration'] = dt
            log_entry_durations['duration_enqueued'] = time_enqueued
            log_entry_durations['timestamp'] = next.utils.datetimeNow()
            ell.log( app_id+':ALG-DURATION', log_entry_durations  )
    else:
        return_value = (args_out_json, didSucceed, message)

    print('#### Finished %s,  time_enqueued=%s,  execution_time=%s ####' % (task_name, time_enqueued, dt))

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

        error = traceback.format_exc()
        log_entry = {'exp_uid': exp_uid, 'task': task_name, 'error': error, 'timestamp': next.utils.datetimeNow()}
        ell.log(app_id+':APP-EXCEPTION', log_entry)

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

