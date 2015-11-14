import next.utils
import hashlib
import bisect

from datetime import datetime,timedelta

import celery
from next.broker.celery_app import tasks as tasks

from next.broker.celery_app.celery_broker import app

import next.constants
import redis
import json
import time
import next.utils as utils

class JobBroker:

    # Initialization method for the broker
    def __init__(self):

        # parameter of consistent hashing. The larger the number, the more uniform the routing gets
        self.num_replicas = 5

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
        result = tasks.apply.apply_async(args=[app_id,exp_uid,task_name, args, submit_timestamp], exchange='async@'+domain, routing_key='async@'+domain)
        if ignore_result:
            return True
        else:
            return result.get(interval=.001) 

    def applySyncByNamespace(self, app_id, exp_uid, task_name, args, namespace=None, ignore_result=False,time_limit=0):
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
        job_uid = utils.getNewUID()
        if time_limit == 0:
            soft_time_limit = None
            hard_time_limit = None
        else:
            soft_time_limit = time_limit
            hard_time_limit = time_limit + .01
        result = tasks.apply_sync_by_namespace.apply_async(args=[app_id,exp_uid,task_name, args, namespace, job_uid, submit_timestamp, time_limit], exchange='sync@'+domain, routing_key='sync@'+domain,soft_time_limit=soft_time_limit,time_limit=hard_time_limit)
        if ignore_result:
            return True
        else:
            return result.get(interval=.001) 

    def __get_domain_for_job(self,job_id):
        """
        Computes which domain to run a given job_id on.
        """
        while not self.r.exists('replicated_domains_hash'):
            print "failed to retrieve domain_hashes from redis"
            time.sleep(.1)

        replicated_domains_hash = json.loads(self.r.get('replicated_domains_hash'))

        h = self.hash(job_id)
        # Edge case where we cycle past hash value of 1 and back to 0.
        if h > replicated_domains_hash[-1][1]: return replicated_domains_hash[0][0]
        # Find the index of the worker
        hash_values = map(lambda x: x[1],replicated_domains_hash)
        index = bisect.bisect_left(hash_values,h)
        return replicated_domains_hash[index][0]


    def refresh_domain_hashes(self):

        # see what workers are out there
        worker_pings = None
        while worker_pings==None:
            try:
                # one could also use app.control.inspect().active_queues()
                worker_pings = app.control.inspect().ping()
            except:
                worker_pings = None
        worker_names = worker_pings.keys()
        domain_names_with_dups = [ item.split('@')[1] for item in worker_names]
        domain_names = list(set(domain_names_with_dups)) # remove duplicates!

        timestamp = utils.datetime2str(utils.datetimeNow())
        print "[ %s ] domains with active workers = %s" % (timestamp,str(domain_names))

        replicated_domains_hash = []
        for domain in domain_names:
            for i in range(self.num_replicas):
                replicated_domains_hash.append((domain, self.hash(domain+'_replica_'+str(i)), i))
        replicated_domains_hash = sorted( replicated_domains_hash, key = lambda x: x[1])  

        self.r.set('replicated_domains_hash',json.dumps(replicated_domains_hash))
    
    def hash(self,key):
        """
        Provides a simple hash of a key between 0 and 1. Used in the consistent hashing scheme.
        """
        return (int(hashlib.md5(key).hexdigest(),16) % 1000000)/1000000.0



    # # TODO
    # def add_worker(self, worker_id):
    # #Add a worker with a given id.
    #     return 0

    # # TODO
    # def remove_worker(self, worker_id):
    # #Remove a worker with a given id.
    #     return 0
    
    # # Completely reshuffle the workers and the jobs they are on
    # def refresh_workers(self):
    # #Refresh the full set of workers.
    #     self.__initialize_worker_hashes()
        
    
