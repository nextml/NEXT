"""
API for interacting with permanent+cache database
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 12/30/2014

This API treats the CacheStore and PermStore themselves as APIs
that are not specific to any one kind of database (e.g. MongoDB/Redis).
The cache is meant to be the 'working' memory which is intermittently sent
to the permanent store. The user of the database does not need to know anything
about how this works but it should be clear from inspecting the individual
functions below.

Note: All functions (e.g. get,set,...) take any python object as input,
converting each object into a string using cPickle before placing it in
the PermStore or CacheStore which expect string values only.

Note: Permstore cannot store large documents (>=16mb) due to JSON store restrictions.
There are easy work around, we just haven't gotten there yet.

In addition to traditional database functions (e.g. exists,get,set,delete)
the API also implements Log functionality. See below for details

Some common functions
###############################

Initialization::\n
    from next.database_client.DatabaseAPI import DatabaseAPI
    db = DatabaseAPI()

App data functions::\n
    doesExist,didSucceed,message = db.exists(bucket_id,doc_uid,key)
    value,didSucceed,message = db.get(bucket_id,doc_uid,key)
    doc,didSucceed,message = db.getDoc(bucket_id,doc_uid)
    doc,didSucceed,message = db.getDocsByPattern(bucket_id,pattern_dict)
    didSucceed,message = db.set(bucket_id,doc_uid,key,value)
    didSucceed,message = db.delete(bucket_id,doc_uid,key)
    didSucceed,message = db.deleteDocsByPattern(bucket_id,pattern_dict)

App data get::\n
    docNames,didSucceed,message = db.getDocNames(bucket_id)
    bucketNames,didSucceed,message = db.getBucketNames()

App data inspection::\n
    description,didSucceed,message = db.inspectDoc(bucket_id,doc_uid)
    description,didSucceed,message = db.inspectDatabase()

App Log functions::\n
    didSucceed,message = db.log(bucket_id,log_entry_dict)
    logs,didSucceed,message = db.getLogsByPattern(bucket_id,pattern_dict)
    logs,didSucceed,message = db.deleteLogsByPattern(bucket_id,pattern_dict)

Maintenance Functions::\n
    didSucceed,message = db.assertConnection()
    didSucceed,message = db.flushDocCache(bucket_id,doc_uid)
    didSucceed,message = db.flushCache()
    db.irreversiblyDeleteEverything()

Log-specific functionality
###############################

System logs
*************
Initializing::\n
    from next.database_client.DatabaseAPI import DatabaseAPI
    import datetime
    db = DatabaseAPI()

Log a dictionary to 'system' with string values, log_dict = {'key1':'value1','key2':'value2'}.
Note that {'timestamp': datetime.now()} is autotmaticaly appended and should NOT be added to log_dict::\n
    didSucceed,message = db.log('system',log_dict)

Retrieve all logs from 'system'::\n
    list_of_log_dict,didSucceed,message = db.getLogsByPattern('system',{})

Retrieve all logs from 'system' that contains the key:value pair {'workerName':'worker4'}::\n
    filter_dict = {'workerName':'worker4'}
    list_of_log_dict,didSucceed,message = db.getLogsByPattern('system',filter_dict)

Retrieve all logs from 'system' that contains the key 'cpu'::\n
    filter_dict = { 'cpu': { '$exists': True } }
    list_of_log_dict,didSucceed,message = db.getLogsByPattern('system',filter_dict)

Retrieve all logs from 'system' between (datetime.datetime) start and (datetime.datetime) end::\n
    import datetime
    start = datetime.datetime(2015, 1, 8, 20, 31, 19, 610000)
    end = datetime.datetime(2015, 1, 12, 0, 0, 0, 000000)
    filter_dict = {'timestamp': { '$gte':start,'$lt':end} }
    list_of_log_dict,didSucceed,message = db.getLogsByPattern('system',filter_dict)

Retrieve all logs from 'system' from the last 30 seconds::\n
    import datetime
    seconds = 30
    start = next.utils.datetimeNow() - datetime.timedelta(0,seconds)
    filter_dict = {'timestamp': { '$gte':start } }
    list_of_log_dict,didSucceed,message = db.getLogsByPattern('system',filter_dict)

Combination of a bunch of all of the above::\n
    import next.utils
    import datetime
    seconds = 3600
    start = next.utils.datetimeNow() - datetime.timedelta(0,seconds)
    filter_dict = { 'timestamp': { '$gte':start }, 'cpu': { '$exists': True }, 'workerName':'worker4' }
    list_of_log_dict,didSucceed,message = db.getLogsByPattern('system',filter_dict)



App logs
***********

Initialize::\n
    from next.database.DatabaseAPI import DatabaseAPI
    import datetime
    db = DatabaseAPI()
    app_id = 'StochasticBanditsPureExploration'
    exp_uid = 'W0DA0DJAD9JAS'
    alg_id = 'LUCB'

Log a dictionary to app_id:exp_uid with string values, log_dict = {'key1':'value1','key2':'value2'}::\n
    from next.logging.LogClient import LogClient

    ell = LogClient(db,app_id,exp_uid) # to log to for management of experiment
    log_dict = { 'type':'API-CALL','task':'initExp' }
    didSucceed = ell.log(log_dict)

or EQUIVALENTLY::\n
    doc_uid = next.utils.getDocUID(exp_uid)
    log_dict = { 'type':'API-CALL','task':'initExp' }
    log_dict.update({'doc_uid':doc_uid,'exp_uid':exp_uid,'app_id':app_id })
    didSucceed,message = db.log(app_id,log_dict)


Log a dictionary to app_id:exp_uid:alg_id with string values, log_dict = {'key1':'value1','key2':'value2'}::\n
    ella = LogClient(db,app_id,exp_uid,alg_id) # to log to for management of algorithm within experiment
    log_dict = { 'type':'ALG-CALL','task':'initExp' }
    didSucceed,message = ella.log(log_dict)

EQUIVALENTLY::\n
    doc_uid = next.utils.getDocUID(exp_uid,alg_id)
    log_dict = { 'type':'ALG-CALL','task':'initExp' }
    log_dict.update({'doc_uid':doc_uid,'exp_uid':exp_uid,'app_id':app_id })
    didSucceed,message = db.log(app_id,log_dict)

Retrieve all logs from app_id::\n
    list_of_log_dict,didSucceed,message = db.getLogsByPattern(app_id,{})

Retrieve all logs involving exp_uid='W0DA0DJAD9JAS' (the management doc and the algorithm docs)::\n
    filter_dict = {'exp_uid':'W0DA0DJAD9JAS'}
    list_of_log_dict,didSucceed,message = db.getLogsByPattern(app_id,filter_dict)

Retrieve all logs involving the management of exp_uid='W0DA0DJAD9JAS'::\n
    doc_uid = next.utils.getDocUID(exp_uid)
    filter_dict = {'doc_uid':doc_uid}
    list_of_log_dict,didSucceed,message = db.getLogsByPattern(app_id,filter_dict)

Retrieve all logs involving the algorithm alg_id='LUCB' of exp_uid='W0DA0DJAD9JAS'::\n
    doc_uid = next.utils.getDocUID(exp_uid,alg_id)
    filter_dict = {'doc_uid':doc_uid}
    list_of_log_dict,didSucceed,message = db.getLogsByPattern(app_id,filter_dict)

Retrieve all logs involving the algorithm alg_id='LUCB' of exp_uid='W0DA0DJAD9JAS' within the last 30 seconds::\n
    import datetime
    seconds = 3000
    start = next.utils.datetimeNow() - datetime.timedelta(0,seconds)
    doc_uid = next.utils.getDocUID(exp_uid,alg_id)
    filter_dict = {'timestamp': { '$gte':start }, 'doc_uid':doc_uid }
    list_of_log_dict,didSucceed,message = db.getLogsByPattern(app_id,filter_dict)

"""

import cPickle
import traceback
from datetime import datetime
import time
from functools import wraps

import numpy as np
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.binary import Binary
from bson.objectid import ObjectId

import next.constants as constants
import next.utils as utils

try:
    import next.broker.broker
except:
    print "Warning: you will not be able to submit jobs to the broker"
    pass

class DatabaseException(BaseException):
    pass

def to_db_fmt(x):
    # recursive descent through lists
    if isinstance(x, list):
        return [to_db_fmt(v) for v in x]

    # recursive descent through dicts
    if isinstance(x, dict):
        return {k: to_db_fmt(v) for k, v in x.items()}

    # convert Numpy arrays to python arrays
    # note: assumes that .tolist() will return only database-acceptable types
    if isinstance(x, np.ndarray):
        return x.tolist()

    # types that MongoDB can natively store
    if type(x) in {int, float, long, complex, str, unicode, datetime}:
        return x

    # interface types. don't repickle these
    if type(x) in {Binary, ObjectId}:
        return x

    # pickle everything else, wrap in MongoDB `Binary`
    return Binary(cPickle.dumps(x, protocol=2))

def from_db_fmt(x):
    # recursive descent through lists
    if isinstance(x, list):
        return [from_db_fmt(v) for v in x]

    # recursive descent through dicts
    if isinstance(x, dict):
        return {k: from_db_fmt(v) for k, v in x.items()}

    if isinstance(x, Binary):
        # this might be pickled data; let's attempt to deserialize it
        try:
            return cPickle.loads(x)
        except cPickle.UnpicklingError:
            # this wasn't pickled data. just return it.
            return x

    # not a datatype we need to deserialize! just pass it out
    return x

class DatabaseAPI(object):
    """
    Serves as an API object that can be passed around. See above for usage

    Attributes:
        client : PyMongo client
    """

    def __init__(self, mongo_host=constants.MONGODB_HOST, mongo_port=constants.MONGODB_PORT):
        self.duration_permStoreSet = 0.0
        self.duration_permStoreGet = 0.0

        self.client = None
        self.connect_mongo(mongo_host, mongo_port)

        self.broker = None

    def __del__(self):
        if self.client is not None:
            self.client.close()

    def timed(op_type='set'):
        def decorator(f):
            @wraps(f)
            def wrapper(self, *args, **kwargs):
                result, dt = utils.timeit(f)(self, *args, **kwargs)

                if op_type == 'set':
                    self.duration_permStoreSet += dt
                elif op_type == 'get':
                    self.duration_permStoreGet += dt

                return result
            return wrapper
        return decorator

    def connect_mongo(self, host, port):
        # Note: w=0 disables write acknowledgement, making PyMongo send writes
        #       without waiting to see if they succeeded
        self.client = MongoClient(host, port, w=0)

        if not self.is_connected():
            raise DatabaseException("Server not available!")

    def is_connected(self):
        try:
            # The `ismaster` command is very cheap and does not require authentication
            self.client.admin.command('ismaster')
            return True
        except ConnectionFailure:
            return False

    def _bucket(self, bucket_id):
        return self.client[constants.app_data_database_id][bucket_id]

    @timed(op_type='get')
    def exists(self,bucket_id,doc_uid,key):
        # if the document isn't found, just set doc to an empty dict,
        # so that any .get(key) call returns None
        doc = self._bucket(bucket_id).find_one({"_id":doc_uid},
            projection={key: True}) or {}
        return doc.get(key) is not None

    @timed(op_type='get')
    def get(self,bucket_id,doc_uid,key):
        val = self._bucket(bucket_id).find_one({"_id": doc_uid}, {key: True}).get(key)
        return from_db_fmt(val)

    @timed(op_type='get')
    def get_many(self,bucket_id,doc_uid,key_list):
        projection = {k: True for k in key_list}
        doc = self._bucket(bucket_id).find_one({"_id": doc_uid}, projection)
        val = {k: doc.get(k) for k in key_list}

        return from_db_fmt(val)

    @timed(op_type='get')
    def get_and_delete(self,bucket_id,doc_uid,key):
        doc = self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$unset': {key: ''}}, projection={key: True})

        return from_db_fmt(doc.get(key))

    @timed(op_type='set')
    def increment(self,bucket_id,doc_uid,key,value=1):
        return self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$inc': {key: value}}, projection={key: True},
            new=True, upsert=True).get(key)

    @timed(op_type='set')
    def increment_many(self,bucket_id,doc_uid,key_value_dict):
        projection = {k: True for k in key_value_dict.keys()}
        values = {k: v for k, v in key_value_dict.items() if v != 0}

        new_doc = self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$inc': values}, projection=projection, new=True, upsert=True)

        return {k: new_doc.get(k) for k in key_value_dict.keys()}

    @timed(op_type='get')
    def get_list(self,bucket_id,doc_uid,key):
        return self.get(bucket_id, doc_uid, key)

    @timed(op_type='get')
    def pop_list(self, bucket_id, doc_uid, key, end):
        # For Mongo's $pop, 1 is the last element and -1 is the first.
        if end == 0:
            mongo_idx = -1
        elif end == -1:
            mongo_idx = 1
        else:
            raise DatabaseException("Can only pop first (index=0) or last (index=-1) element of list!")

        val = self._bucket(bucket_id).find_and_modify({"_id": doc_uid},
            {'$pop': {key: mongo_idx}}).get(key)

        return from_db_fmt(val[end])

    @timed(op_type='set')
    def append_list(self,bucket_id,doc_uid,key,value):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$push': {key: to_db_fmt(value)}}, upsert=True)

    @timed(op_type='set')
    def set_list(self,bucket_id,doc_uid,key,value):
        self.set(bucket_id, doc_uid, key, value)

    @timed(op_type='set')
    def set_doc(self,bucket_id,doc_uid,doc):
        if doc_uid:
            doc['_id'] = doc_uid
        self._bucket(bucket_id).replace_one({"_id": doc_uid}, to_db_fmt(doc), upsert=True)

    @timed(op_type='get')
    def get_doc(self,bucket_id,doc_uid):
        return from_db_fmt(self._bucket(bucket_id).find_one({"_id": doc_uid}))

    @timed(op_type='get')
    def get_docs_with_filter(self,bucket_id,pattern_dict):
        docs_cursor = self._bucket(bucket_id).find(pattern_dict)

        return [from_db_fmt(doc) for doc in docs_cursor]

    @timed(op_type='set')
    def set(self,bucket_id,doc_uid,key,value):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$set': {key: to_db_fmt(value)}}, upsert=True)

    @timed(op_type='set')
    def set_many(self,bucket_id,doc_uid,key_value_dict):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$set': to_db_fmt(key_value_dict)})

    @timed(op_type='set')
    def delete(self,bucket_id,doc_uid,key):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$unset': {key: True}})

    def ensure_index(self,bucket_id,index_dict):
        didSucceed,message = self.permStore.create_index(constants.app_data_database_id,bucket_id,index_dict)
        return didSucceed,message

    def drop_all_indexes(self,bucket_id):
        didSucceed,message = self.permStore.drop_all_indexes(constants.app_data_database_id,bucket_id)
        return didSucceed,message

    def delete_docs_with_filter(self,bucket_id,pattern_dict):
        docs,didSucceed,message = self.permStore.getDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)
        return self.permStore.deleteDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)

    def submit_job(self,app_id,exp_uid,task,task_args_json,namespace=None,ignore_result=True,time_limit=0, alg_id=None, alg_label=None):
        if self.broker == None:
            self.broker = next.broker.broker.JobBroker()
        if namespace==None:
            result = self.broker.applyAsync(app_id,exp_uid,task,task_args_json,ignore_result=ignore_result)
        else:
            result = self.broker.applySyncByNamespace(app_id,exp_uid,
                                                      alg_id, alg_label,
                                                      task,task_args_json,namespace=namespace,
                                                      ignore_result=ignore_result,time_limit=time_limit)
        return result

