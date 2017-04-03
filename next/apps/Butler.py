import next.utils as utils
import numpy as np
import os
import next.constants as constants
import redis
import StringIO

class Memory(object):
    def __init__(self):
        # utils.debug_print(constants.MINIONREDIS_PORT, constants.MINIONREDIS_PORT)
        self.cache = None
        self.max_entry_size = 500000000 # 500MB

    def ensure_connection(self):
        if self.cache is None:
            self.cache = redis.StrictRedis(host=constants.MINIONREDIS_HOST, port=constants.MINIONREDIS_PORT)

    def num_entries(self, size):
        if size % self.max_entry_size == 0:
            return size / self.max_entry_size
        else:
            return (size / self.max_entry_size) + 1
        
    def set(self, key, value):
        self.ensure_connection()
        try:
            n = self.num_entries(len(value))
            utils.debug_print("Setting ",len(value),"bytes in",n,"entries")
            for i in range(n):
                k = key + ":" + str(i)
                self.cache.set(k,value[i*self.max_entry_size:(i+1)*self.max_entry_size])
            return self.cache.set(key,"{}:{}".format(str(n),str(len(value))))
        except Exception as exc:
            utils.debug_print("REDIS OOPS: ",exc)
            return False

    def set_file(self, key, f):
        self.ensure_connection()

        try:
            f.seek(0,os.SEEK_END)
            l = f.tell()
            f.seek(0, 0)
            n = self.num_entries(l)
            utils.debug_print("Setting ",l,"bytes in",n,"entries")
            for i in range(n):
                k = key + ":" + str(i)
                v = f.read(self.max_entry_size)
                self.cache.set(k,v)
            return self.cache.set(key,"{}:{}".format(str(n),str(l)))
        except Exception as exc:
            utils.debug_print("REDIS OOPS: ",exc)
            return False

    def get(self, key):
        self.ensure_connection()
        d =  self.cache.get(key)
        n,l = d.split(":")
        l = int(l)
        n = int(n)
        ans = ""
        utils.debug_print("Getting ",l,"bytes in",n,"entries")
        for i in range(n):
            k = key + ":" + str(i)
            ans += self.cache.get(k)
        return ans
    
    def get_file(self, key):
        self.ensure_connection()
        d =  self.cache.get(key)
        f = StringIO.StringIO()
        n,l = d.split(":")
        l = int(l)
        n = int(n)
        ans = ""
        utils.debug_print("Getting ",l,"bytes in",n,"entries")
        for i in range(n):
            k = key + ":" + str(i)
            f.write(self.cache.get(k))
        f.seek(0, 0)
        return f

    def lock(self, name, **kwargs):
        self.ensure_connection()
        return self.cache.lock(name, **kwargs)
    
    def exists(self, key):
        self.ensure_connection()
        return self.cache.exists(key)


class Collection(object):
    def __init__(self, collection, uid_prefix, exp_uid, db, timing=True):
        self.collection = collection
        self.db = db
        self.exp_uid = exp_uid
        self.uid_prefix = uid_prefix
        self.get_durations = 0.0
        self.set_durations = 0.0
        self.timing = timing

    def set(self, uid="", key=None, value=None, exp=None):
        """
        Set an object in the collection, or an entry in an object in the collection.
        * key == None:    collection[uid] = value
        * key != None:    collection[uid][key] = value
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        if not key:
            self.timed(self.db.set_doc)(self.collection, uid, value)
        else:
            self.timed(self.db.set)(self.collection, uid, key, value)

    def set_many(self, uid="", key_value_dict=None, exp=None):
        """
        For each key in key_value_dict, sets value by key_value_dict[key]
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        return self.timed(self.db.set_many)(self.collection, uid, key_value_dict)

    def get(self, uid="", key=None, pattern=None, exp=None):
        """
        Get an object from the collection (possibly by pattern), or an entry (or entries) from an object in the collection.
        * key == None and pattern == None:                         return collection[uid]
        * key != None and pattern == None and type(key) != list:   return collection[uid][key]
        * key != None and pattern == None and type(key) == list:   return {k: collection[uid][k] for k in key}
        * pattern != None:                                         return collection[uid] matching pattern
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        if key==None and pattern==None:
            return self.timed(self.db.get_doc, get=True)(self.collection, uid)
        elif key:
            if(type(key) == list):
                return self.timed(self.db.get_many, get=True)(self.collection, uid, key)
            else:
                return self.timed(self.db.get, get=True)(self.collection, uid, key)
        else:
            return self.timed(self.db.get_docs_with_filter, get=True)(self.collection, pattern)

    def get_and_delete(self, uid="", key=None, exp=None):
        """
        Get a value from the collection corresponding to the key and then delete the (key,value).
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        value = self.timed(self.db.get_and_delete, get=True)(self.collection, uid, key)
        return value

    def exists(self, uid="", key='_id', exp=None):
        """
        Check if an object with the specified uid exists
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        result = self.timed(self.db.exists, get=True)(self.collection, uid, key)
        print "Butler.py:exist, exist check", uid, key, result
        return result#self.timed(self.db.exists,get=True)(self.collection, uid, key)

    def increment(self, uid="", key=None, exp=None, value=1):
        """
        Increment a value (or values) in the collection.
        * key = str:   increment collection[uid][key]

        * value: How much the value should be incremented by.
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        return self.timed(self.db.increment, get=True)(self.collection, uid, key, value)

    def increment_many(self, uid="", key_value_dict=None, exp=None):
        """
        For each key in key_value_dict, increments value by key_value_dict[key]

        * values: How much the value should be incremented by.
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        return self.timed(self.db.increment_many, get=True)(self.collection, uid, key_value_dict)

    def append(self, uid="", key=None, value=None, exp=None):
        """
        Append a value to collection[uid][key] (which is assumed to be a list)
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        self.timed(self.db.append_list)(self.collection, uid, key, value)

    def pop(self, uid="", key=None, value=-1, exp=None):
        """
        Pop a value from collection[uid][key] (which is assumed to be a list)
        value=-1 pops the last element of the list (default)
        value=0 pops the first element of the list
        Other values for "value" will throw error and return a None (not supported in Mongo)
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        return self.timed(self.db.pop_list, get=True)(self.collection, uid, key, value)

    def getDurations(self):
        """
        For book keeping purposes only
        """
        return {'duration_dbSet': self.set_durations, 'duration_dbGet' : self.get_durations}

    def timed(self, f, get=False):
        if not self.timing:
            return f

        def timed_f(*args, **kw):
            result,dt = utils.timeit(f)(*args, **kw)
            res = None
            if(get):
                self.get_durations += dt
                res, didSucceed, message = result
            else:
                self.set_durations += dt
                didSucceed, message = result
            return res
        return timed_f

class Butler(object):
    def __init__(self, app_id, exp_uid, targets, db, ell, alg_label=None, alg_id=None):
        self.app_id = app_id
        self.exp_uid = exp_uid
        self.alg_label = alg_label
        self.alg_id = alg_id
        self.db = db
        self.ell = ell
        self.targets = targets
        self.memory = Memory()
        
        if self.targets.db==None:
            self.targets.db = self.db
        self.queries = Collection(self.app_id+":queries", "", self.exp_uid, db)
        self.admin = Collection("experiments_admin", "", self.exp_uid, db)
        self.experiment = Collection(self.app_id+":experiments", "{exp_uid}", self.exp_uid, db)
        if alg_label is None:
            self.algorithms = Collection(self.app_id+":algorithms", "{exp_uid}_", self.exp_uid, db)
        else:
            self.algorithms = Collection(self.app_id+":algorithms", "{exp_uid}_"+alg_label, self.exp_uid, db)
        self.participants = Collection(self.app_id+":participants", "", self.exp_uid, db)
        self.dashboard = Collection(self.app_id+":dashboard", "", self.exp_uid, db)
        self.other = Collection(self.app_id+":other", "{exp_uid}_", self.exp_uid, db)

    def log(self, log_name, log_value):
        self.ell.log(self.app_id+":"+log_name, log_value)

    def job(self, task, task_args_json, ignore_result=True, time_limit=0):
        if self.alg_label:
            self.db.submit_job(self.app_id, self.exp_uid,
                               task, task_args_json,
                               self.exp_uid + '_' + self.alg_label,
                               ignore_result, time_limit,
                               alg_id=self.alg_id, alg_label=self.alg_label)  
        else:
            self.db.submit_job(self.app_id, self.exp_uid, task, task_args_json, None, ignore_result, time_limit)  

