import os
import StringIO
from functools import wraps

import redis

import next.constants as constants
import next.utils as utils


class Memory(object):
    def __init__(self, collection='', exp_uid=''):
        self.key_prefix = collection + exp_uid
        self.cache = None
        self.max_entry_size = 500000000  # 500MB

    def check_prefix(self):
        if self.key_prefix == '':
            utils.debug_print("butler.memory is deprecated."
                              " Change to butler.experiment.memory or butler.algorithm.memory, etc."
                              " wherever appropriate")

    def ensure_connection(self):
        try:
            if self.cache is None:
                self.cache = redis.StrictRedis(host=constants.MINIONREDIS_HOST, port=constants.MINIONREDIS_PORT)
        except Exception as e:
            raise Exception("Butler.Collection.Memory could not connect with RedisDB: {}".format(e))

    def num_entries(self, size):
        if size % self.max_entry_size == 0:
            return size / self.max_entry_size
        else:
            return (size / self.max_entry_size) + 1
        
    def set(self, key, value):
        self.check_prefix()
        key = self.key_prefix + key
        try:
            self.ensure_connection()
            l = len(value)
            n = self.num_entries(l)
            utils.debug_print("Setting {} in {} entries".format(l, n))
            for i in range(n):
                k = key + ":" + str(i)
                self.cache.set(k, value[i*self.max_entry_size:(i+1)*self.max_entry_size])
            return self.cache.set(key, "{}:{}".format(str(n), str(l)))
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.set exception: {}".format(e))
            return False

    def set_file(self, key, f):
        self.check_prefix()
        key = self.key_prefix + key
        try:
            self.ensure_connection()
            f.seek(0, os.SEEK_END)
            l = f.tell()
            f.seek(0, 0)
            n = self.num_entries(l)
            utils.debug_print("Setting {} bytes in {} entries".format(l, n))
            for i in range(n):
                k = key + ":" + str(i)
                v = f.read(self.max_entry_size)
                self.cache.set(k, v)
            return self.cache.set(key, "{}:{}".format(str(n), str(l)))
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.set_file exception: {}".format(e))
            return False

    def get(self, key):
        self.check_prefix()
        try:
            self.ensure_connection()
            key = self.key_prefix + key
            d = self.cache.get(key)
            n, l = d.split(":")
            l = int(l)
            n = int(n)
            ans = ""
            utils.debug_print("Getting {} bytes in {} entries".format(l, n))
            for i in range(n):
                k = key + ":" + str(i)
                ans += self.cache.get(k)
            return ans
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.get exception: {}".format(e))
            return None

    def get_file(self, key):
        self.check_prefix()
        try:
            self.ensure_connection()
            key = self.key_prefix + key
            d = self.cache.get(key)
            f = StringIO.StringIO()
            n, l = d.split(":")
            l = int(l)
            n = int(n)
            utils.debug_print("Getting {} bytes in {} entries".format(l, n))
            for i in range(n):
                k = key + ":" + str(i)
                f.write(self.cache.get(k))
            f.seek(0, 0)
            return f
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.get_file exception: {}".format(e))
            return None

    def lock(self, name, **kwargs):
        try:
            self.ensure_connection()
            name = self.key_prefix + name
            return self.cache.lock(name, **kwargs)
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.lock exception: {}".format(e))
            return None
    
    def exists(self, key):
        try:
            self.ensure_connection()
            key = self.key_prefix + key
            return self.cache.exists(key)
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.exists exception: {}".format(e))
            return None


class Collection(object):
    def __init__(self, collection, uid_prefix, exp_uid, db, timing=True):
        self.collection = collection
        self.db = db
        self.exp_uid = exp_uid
        self.uid_prefix = uid_prefix
        self.get_durations = 0.0
        self.set_durations = 0.0
        self.timing = timing
        self.memory = Memory(collection, exp_uid)

    def timed(op_type='set'):
        def decorator(f):
            @wraps(f)
            def wrapper(self, *args, **kwargs):
                result, dt = utils.timeit(f)(self, *args, **kwargs)

                if op_type == 'set':
                    self.set_durations += dt
                elif op_type == 'get':
                    self.get_durations += dt

                return result
            return wrapper
        return decorator


    @timed
    def set(self, uid="", key=None, value=None, exp=None):
        """
        Set an object in the collection, or an entry in an object in the collection.
        * key == None:    collection[uid] = value
        * key != None:    collection[uid][key] = value
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        if not key:
            self.db.set_doc(self.collection, uid, value)
        else:
            self.db.set(self.collection, uid, key, value)

    @timed
    def set_many(self, uid="", key_value_dict=None, exp=None):
        """
        For each key in key_value_dict, sets value by key_value_dict[key]
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        return self.db.set_many(self.collection, uid, key_value_dict)

    @timed(op_type='get')
    def get(self, uid="", key=None, pattern=None, exp=None):
        """
        Get an object from the collection (possibly by pattern), or an entry (or entries) from an object in the collection.
        * key == None and pattern == None:                         return collection[uid]
        * key != None and pattern == None and type(key) != list:   return collection[uid][key]
        * key != None and pattern == None and type(key) == list:   return {k: collection[uid][k] for k in key}
        * pattern != None:                                         return collection[uid] matching pattern
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        if key is None and pattern is None:
            return self.db.get_doc(self.collection, uid)
        elif key:
            if isinstance(key, list):
                return self.db.get_many(self.collection, uid, key)
            else:
                return self.db.get(self.collection, uid, key)
        else:
            return self.db.get_docs_with_filter(self.collection, pattern)
    
    @timed(op_type='get')
    def get_and_delete(self, uid="", key=None, exp=None):
        """
        Get a value from the collection corresponding to the key and then delete the (key,value).
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        value = self.db.get_and_delete(self.collection, uid, key)
        return value

    @timed(op_type='get')
    def exists(self, uid="", key='_id', exp=None):
        """
        Check if an object with the specified uid exists
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        return self.db.exists(self.collection, uid, key)

    @timed(op_type='get')
    def increment(self, uid="", key=None, exp=None, value=1):
        """
        Increment a value (or values) in the collection.
        * key = str:   increment collection[uid][key]

        * value: How much the value should be incremented by.
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        return self.db.increment(self.collection, uid, key, value)

    @timed(op_type='get')
    def increment_many(self, uid="", key_value_dict=None, exp=None):
        """
        For each key in key_value_dict, increments value by key_value_dict[key]

        * values: How much the value should be incremented by.
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp is None else exp))
        return self.db.increment_many(self.collection, uid, key_value_dict)

    @timed
    def append(self, uid="", key=None, value=None, exp=None):
        """
        Append a value to collection[uid][key] (which is assumed to be a list)
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        self.db.append_list(self.collection, uid, key, value)

    @timed(op_type='get')
    def pop(self, uid="", key=None, value=-1, exp=None):
        """
        Pop a value from collection[uid][key] (which is assumed to be a list)
        value=-1 pops the last element of the list (default)
        value=0 pops the first element of the list
        Other values for "value" will throw error and return a None (not supported in Mongo)
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        return self.db.pop_list(self.collection, uid, key, value)

    def getDurations(self):
        """
        For book keeping purposes only
        """
        return {'duration_dbSet': self.set_durations, 'duration_dbGet': self.get_durations}


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
        
        if self.targets.db is None:
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
