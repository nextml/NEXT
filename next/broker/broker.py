import next.utils as utils

from datetime import datetime,timedelta

import celery
from next.broker.celery_app import tasks as tasks

from next.broker.celery_app.celery_broker import app

import os

import next.constants
import redis
import json
import time
import next.utils as utils

class JobBroker:

    # Initialization method for the broker
    def __init__(self):

        self.hostname = None

        # location of hashes
        self.r = redis.StrictRedis(host=next.constants.RABBITREDIS_HOSTNAME, port=next.constants.RABBITREDIS_PORT, db=0)

    def applyAsync(self, app_id, exp_uid, task_name, args, ignore_result=False):
        """
        Run a task (task_name) on a set of args with a given app_id, and exp_uid.
        Waits for computation to finish and returns the answer unless ignore_result=True in which case its a non-blocking call.
        No guarantees about order of execution.

        Inputs: ::\n
            (string) app_id, (string) exp_id, (string) task_name, (json) args
        Outputs: ::\n
            task_name(app_id, exp_id, args)

        """
        submit_timestamp = utils.datetimeNow('string')
        domain = self.__get_domain_for_job(app_id+"_"+exp_uid)
        if next.constants.CELERY_ON:
            result = tasks.apply.apply_async(args=[app_id,
                                                   exp_uid,
                                                   task_name,
                                                   args,
                                                   submit_timestamp],
                                             exchange='async@'+domain,
                                             routing_key='async@'+domain)
            if ignore_result:
                return True
            else:
                return result.get(interval=0.001)
        else:
            result = tasks.apply(app_id,exp_uid,task_name, args, submit_timestamp)
            if ignore_result:
                return True
            else:
                return result

    def dashboardAsync(self, app_id, exp_uid, args, ignore_result=False):
        """
        Run a task (task_name) on a set of args with a given app_id, and exp_uid.
        Waits for computation to finish and returns the answer unless ignore_result=True in which case its a non-blocking call.
        No guarantees about order of execution.

        Inputs: ::\n
            (string) app_id, (string) exp_id, (string) task_name, (json) args
        Outputs: ::\n
            task_name(app_id, exp_id, args)

        """
        submit_timestamp = utils.datetimeNow('string')
        domain = self.__get_domain_for_job(app_id+"_"+exp_uid)

        if next.constants.CELERY_ON:

            result = tasks.apply_dashboard.apply_async(args=[app_id,
                                                             exp_uid,
                                                             args,
                                                             submit_timestamp],
                                                       exchange='dashboard@'+domain,
                                                       routing_key='dashboard@'+domain)
            if ignore_result:
                return True
            else:
                return result.get(interval=0.001)
        else:

            result = tasks.apply_dashboard(app_id,exp_uid, args, submit_timestamp)
            if ignore_result:
                return True
            else:
                return result


    def applySyncByNamespace(self, app_id, exp_uid, alg_id, alg_label, task_name, args, namespace=None, ignore_result=False,time_limit=0):
        """
        Run a task (task_name) on a set of args with a given app_id, and exp_uid asynchronously.
        Waits for computation to finish and returns the answer unless ignore_result=True in which case its a non-blocking call.
        If this method is called a sequence of times with the same namespace (defaults to exp_uid if not set) it is guaranteed that they will execute in order, each job finishing before the next begins

        Inputs: ::\n
            (string) app_id, (string) exp_id, (string) task_name, (json) args

        """
        submit_timestamp = utils.datetimeNow('string')
        if namespace==None:
            namespace=exp_uid
        domain = self.__get_domain_for_job(app_id+"_"+exp_uid)
        num_queues = next.constants.CELERY_SYNC_WORKER_COUNT

        # assign namespaces to queues (with worker of concurrency 1) in round-robbin
        try:
            namespace_cnt = int(self.r.get(namespace+"_cnt"))
        except:
            pipe = self.r.pipeline(True)
            while 1:
                try:
                    pipe.watch(namespace+"_cnt","namespace_counter")
                    if not pipe.exists(namespace+"_cnt"):
                        if not pipe.exists('namespace_counter'):
                            namespace_counter = 0
                        else:
                            namespace_counter = pipe.get('namespace_counter')
                        pipe.multi()
                        pipe.set(namespace+"_cnt",int(namespace_counter)+1)
                        pipe.set('namespace_counter',int(namespace_counter)+1)
                        pipe.execute()
                    else:
                        pipe.unwatch()
                    break
                except redis.exceptions.WatchError:
                    continue
                finally:
                    pipe.reset()
            namespace_cnt = int(self.r.get(namespace+"_cnt"))
        queue_number = (namespace_cnt % num_queues) + 1

        queue_name = 'sync_queue_'+str(queue_number)+'@'+domain
        job_uid = utils.getNewUID()
        if time_limit == 0:
            soft_time_limit = None
            hard_time_limit = None
        else:
            soft_time_limit = time_limit
            hard_time_limit = time_limit + .01
        if next.constants.CELERY_ON:
            result = tasks.apply_sync_by_namespace.apply_async(args=[app_id,exp_uid,
                                                                     alg_id,alg_label,
                                                                     task_name, args,
                                                                     namespace, job_uid,
                                                                     submit_timestamp, time_limit],
                                                               queue=queue_name,
                                                               soft_time_limit=soft_time_limit,
                                                               time_limit=hard_time_limit)
            if ignore_result:
                return True
            else:
                return result.get(interval=.001)
        else:
            result = tasks.apply_sync_by_namespace(app_id,exp_uid,alg_id,alg_label,task_name, args, namespace, job_uid, submit_timestamp, time_limit)
            if ignore_result:
                return True
            else:
                return result

    def __get_domain_for_job(self, job_id):
        """
        Computes which domain to run a given job_id on.
        Git Commit: c1e4f8aacaa42fae80e111979e3f450965643520 has support
        for multiple worker nodes. See the code in broker.py, cluster_monitor.py, and the docker-compose
        file in that commit to see how to get that up and running. It uses
        a simple circular hashing scheme to load balance getQuery/processAnswer calls.
        This implementation assumes just a single master node and no workers
        so only a single hostname (e.g. localhost) has celery workers.
        """
        if self.r.exists('MINIONWORKER_HOSTNAME'):
            self.hostname = self.r.get('MINIONWORKER_HOSTNAME')
            utils.debug_print('Found hostname: {} (Redis)'.format(self.hostname))
        else:
            with open('/etc/hosts', 'r') as fid:
                for line in fid:
                    if 'MINIONWORKER' in line:
                        self.hostname = line.split('\t')[1].split(' ')[1]
                        self.r.set('MINIONWORKER_HOSTNAME', self.hostname, ex=360)  # expire after 10 minutes
                        utils.debug_print('Found hostname: {} (/etc/hosts)'.format(self.hostname))
                        break
        if self.hostname is None:
            import socket
            self.hostname = socket.gethostname()
            self.r.set('MINIONWORKER_HOSTNAME', self.hostname, ex=360)  # expire after 10 minutes
            utils.debug_print('Found hostname: {} (socket.gethostname())'.format(self.hostname))

        return self.hostname
