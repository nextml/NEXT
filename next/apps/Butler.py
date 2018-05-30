import os
import sys
import StringIO
from functools import wraps
import pickle
import numpy as np
import traceback
import time
import ast
import inspect
from pprint import pprint
from functools import partial
import itertools

import redis

import next.constants as constants
import next.utils as utils


def mem_except_wrap(func):
    def f(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            utils.debug_print("Butler.Collection.Memory.get exception: {}".format(e))
            utils.debug_print(traceback.format_exc())
    return f


class Memory(object):
    def __init__(self, collection='', exp_uid='', uid_prefix=''):
        self.key_prefix = collection + uid_prefix.format(exp_uid=exp_uid)
        self.cache = None
        self.max_entry_size = 500000000  # 500MB
        fns = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, fn in fns:
            if name[0] == '_' or 'ensure_connection' in name:
                continue
            self.name = self._check_prefix(self._ensure_connection(fn))

    def _check_prefix(self, fn=None):
        def f(*args, **kwargs):
            if self.key_prefix == '':
                utils.debug_print("butler.memory is deprecated."
                                  " Change to butler.experiment.memory or butler.algorithm.memory, etc."
                                  " wherever appropriate")
            return fn(*args, **kwargs)
        return f

    def _ensure_connection(self, fn=None):
        if self.cache is None:
            self.cache = redis.StrictRedis(host='minionredis_1')
        return fn


    def _num_entries(self, size):
        if size % self.max_entry_size == 0:
            return size / self.max_entry_size
        else:
            return (size / self.max_entry_size) + 1

    @mem_except_wrap
    def set(self, key=None, value=None, uid='', verbose=True):
        key = self.key_prefix + key + uid
        l = sys.getsizeof(value)
        if l < self.max_entry_size and not isinstance(value, np.ndarray):
            return self.cache.set(key, value)
        value = pickle.dumps(value)
        n = self._num_entries(l)
        if verbose:
            utils.debug_print("Butler.py memory setting {} in {} entries".format(l, n))
        for i in range(n):
            k = key + ":" + str(i)
            self.cache.set(k, value[i*self.max_entry_size:(i+1)*self.max_entry_size])
        return self.cache.set(key, "__redis_set__" + "{}:{}".format(str(n), str(l)))

    @mem_except_wrap
    def set_file(self, key, f, verbose=False):
        key = self.key_prefix + key
        f.seek(0, os.SEEK_END)
        l = f.tell()
        f.seek(0, 0)
        n = self._num_entries(l)
        if verbose:
            utils.debug_print("butler.py memory setting {} bytes in {} entries".format(l, n))
        for i in range(n):
            k = key + ":" + str(i)
            v = f.read(self.max_entry_size)
            self.cache.set(k, v)
        return self.cache.set(key, "{}:{}".format(str(n), str(l)))

    @mem_except_wrap
    def get(self, key=None, uid='', verbose=False):
        key = self.key_prefix + key + uid
        d = self.cache.get(key)
        msg = '__redis_set__'
        pickled = isinstance(d, str) and len(d) >= len(msg) and d[:len(msg)] == msg
        if not pickled:
            return self._from_db_fmt(d)

        d = d[len(msg):]
        n, l = d.split(":")
        l = int(l)
        n = int(n)
        ans = ""
        if verbose:
            utils.debug_print("Getting {} bytes in {} entries".format(l, n))
        for i in range(n):
            k = key + ":" + str(i)
            ans += self.cache.get(k)
        return pickle.loads(ans)

    @mem_except_wrap
    def get_file(self, key):
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

    @mem_except_wrap
    def lock(self, name, **kwargs):
        name = self.key_prefix + name
        return self.cache.lock(name, **kwargs)

    @mem_except_wrap
    def exists(self, key, uid=''):
        key = self.key_prefix + key + uid
        return self.cache.exists(key)

    @mem_except_wrap
    def append(self, key=None, value=None, uid=''):
        if not isinstance(value, list):
            value = [value]
        if not self.exists(key, uid=uid):
            old = "[]"
        else:
            old_key = self.key_prefix + key + uid
            old = self.cache.get(old_key)
        old = ast.literal_eval(old)

        key = self.key_prefix + key + uid
        return self.cache.set(key, old + value)

    @mem_except_wrap
    def increment(self, key=None, value=1, uid=''):
        key = key + uid
        key = self.key_prefix + key
        return self.cache.incr(key, amount=value)

    @mem_except_wrap
    def set_many(self, key_value_dict=None, uid=''):
        with self.cache.pipeline() as pipe:
            for k, v in key_value_dict.items():
                k = self.key_prefix + k + uid
                v = self._to_db_fmt(v)
                pipe.set(k, v)
            ret = pipe.execute()
        return ret

    @mem_except_wrap
    def get_many(self, key=None, uid=''):
        keys = [k for k in key]
        with self.cache.pipeline() as pipe:
            out = []
            for key in keys:
                key = self.key_prefix + key + uid
                pipe.get(key)
            values = pipe.execute()
        return {k: self._from_db_fmt(v) for k, v in zip(keys, values)}

    @mem_except_wrap
    def pipeline(self):
        """
        Returns redis pipeline. Get values with pipe.execute(),
        close with pipe.close()
        """
        return self.cache.pipeline()

    def _to_db_fmt(self, v):
        if isinstance(v, np.ndarray):
            return pickle.dumps(v)
        return v

    def _from_db_fmt(self, v):
        try:
            return ast.literal_eval(v)
        except:
            try:
                return pickle.loads(v)
            except:
                return v


class Collection(object):
    def __init__(self, collection, uid_prefix, exp_uid, db, timing=True):
        self.collection = collection
        self.db = db
        self.exp_uid = exp_uid
        self.uid_prefix = uid_prefix
        self.get_durations = 0.0
        self.set_durations = 0.0
        self.timing = timing
        self.memory = Memory(collection, exp_uid, uid_prefix)

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


    @timed(op_type='set')
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

    @timed(op_type='set')
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

    def get_many(self, **kwargs):
        return self.get(**kwargs)

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

    @timed(op_type='set')
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
            res = self.db.submit_job(self.app_id, self.exp_uid,
                               task, task_args_json,
                               self.exp_uid + '_' + self.alg_label,
                               ignore_result, time_limit,
                               alg_id=self.alg_id, alg_label=self.alg_label)
        else:
            res = self.db.submit_job(self.app_id, self.exp_uid, task, task_args_json, None, ignore_result, time_limit)

        if not ignore_result:
            return res
