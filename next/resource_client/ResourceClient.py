"""
API Client for interacting with resources
Example usage: ::\n
"""

import next.constants
import next.utils as utils
import json
import requests

class ResourceClient(object):
    def __init__(self,app_id,exp_uid,alg_uid,db_api):
        self.app_id = app_id
        self.exp_uid = exp_uid
        self.alg_uid = alg_uid
        self.bucket_id = app_id+':algorithms'
        self.doc_uid = alg_uid

        self.durationSet = 0.0
        self.durationGet = 0.0

        self.db = db_api

    def exists(self,key):
        exists,didSucceed,message,dt = utils.timeit(self.db.exists)(self.bucket_id,self.doc_uid,key)
        self.durationGet += dt
        return exists

    def get(self,key):
        value,didSucceed,message,dt = utils.timeit(self.db.get)(self.bucket_id,self.doc_uid,key)
        self.durationGet += dt
        return value

    def set(self,key,value):
        didSucceed,message,dt = utils.timeit(self.db.set)(self.bucket_id,self.doc_uid,key,value)
        self.durationSet += dt
        return True

    def delete(self,key):
        didSucceed,message,dt = utils.timeit(self.db.delete)(self.bucket_id,self.doc_uid,key)
        self.durationSet += dt
        return True

    def get_many(self,key_list):
        """
        key_list is a (list) of (string) keys. 
        get_many returns dictionary with { key:value } for each key in key_list - all values retrieved simultaneously 
        If requested key does not exist, the key will not exist in the returned dictionary
        """
        return_dict,didSucceed,message,dt = utils.timeit(self.db.get_many)(self.bucket_id,self.doc_uid,key_list)
        self.durationGet += dt
        return return_dict

    def increment(self,key,value=1):
        """
        Atomic increment. Value can be integer or float. 
        To initialize 'counter' at value X: rc.increment('counter',X) 
        Returned value is the value of the key after increment has taken affect
        """
        new_value,didSucceed,message,dt = utils.timeit(self.db.increment)(self.bucket_id,self.doc_uid,key,value)
        self.durationSet += dt
        return new_value

    def increment_many(self,key_value_dict):
        """
        Increments many keys simultaneously.
        Example:
            increment_many({'Xsum':.65,'T':1})
            increment_many({'Xsum':.32,'T':1})
            increment_many({'Xsum':.45,'T':1})

            data = get_many(['Xsum','T'])
            empirical_mean = data['Xsum'] / data['T']
        """
        didSucceed,message,dt = utils.timeit(self.db.increment_many)(self.bucket_id,self.doc_uid,key_value_dict)
        self.durationSet += dt
        return True

    def append_list(self,key,value):
        """
        atomically append a value to a list with key 
        List is initialized when first value is appended: rc.append_list('answer_pairs',(index,answer))
        """
        didSucceed,message,dt = utils.timeit(self.db.append_list)(self.bucket_id,self.doc_uid,key,value)
        self.durationSet += dt
        return True

    def get_list(self,key):
        """
        retrieve list that was initialized and appeneded to by append_list
        """
        value_list,didSucceed,message,dt = utils.timeit(self.db.get_list)(self.bucket_id,self.doc_uid,key)
        self.durationGet += dt
        return value_list

    def daemonProcess(self,daemon_args,time_limit=300):
        """
        DaemonProcess executes submission in order, the next task only starting after the previous task has finished. 
        These tasks are executed in a distributed fashion through the use of locks. 
        This means that if the daemon process hits an edge case and enters an infinite loop or the process throws an exception, 
        the lock may not be successfully released (we do some exception handling but shit happens). Be safe, please set a time_limit 
        on your daemonProcess. If the task is still executing after this time, we will forcefully kill it without notice. 
        Maximum time_limit before a kill signal is sent defaults to 5 minutes.  
        """
        daemonProcess_args_dict = {'alg_uid':self.alg_uid,'daemon_args':daemon_args}
        daemonProcess_args_json = json.dumps(daemonProcess_args_dict)

        self.db.submit_job(self.app_id,self.exp_uid,'daemonProcess',daemonProcess_args_json,namespace=self.alg_uid,ignore_result=True,time_limit=time_limit)

        
    def getDurations(self):
        """
        For book keeping purposes only
        """
        timeDurations = {}
        timeDurations['duration_dbSet'] = self.durationSet
        timeDurations['duration_dbGet'] = self.durationGet
        return timeDurations

