"""
Layer for interfacing with Mongo.

Rewritten by: Liam Marshall <limarshall@wisc.edu>, 2017/04/19
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

    def __init__(self, mongo_host=constants.MONGODB_HOST, mongo_port=constants.MONGODB_PORT,
                    database_name=constants.app_data_database_id):
        self.client = None
        self.connect_mongo(mongo_host, mongo_port)

        self.db_name = database_name

        self.broker = None

    def __del__(self):
        if self.client is not None:
            self.client.close()

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
        return self.client[self.db_name][bucket_id]

    def exists(self,bucket_id,doc_uid,key):
        # if the document isn't found, just set doc to an empty dict,
        # so that any .get(key) call returns None
        doc = self._bucket(bucket_id).find_one({"_id":doc_uid},
            projection={key: True}) or {}
        return doc.get(key) is not None

    def get(self,bucket_id,doc_uid,key):
        val = self._bucket(bucket_id).find_one({"_id": doc_uid}, {key: True}).get(key)
        return from_db_fmt(val)

    def get_many(self,bucket_id,doc_uid,key_list):
        projection = {k: True for k in key_list}
        doc = self._bucket(bucket_id).find_one({"_id": doc_uid}, projection)
        val = {k: doc.get(k) for k in key_list}

        return from_db_fmt(val)

    def get_and_delete(self,bucket_id,doc_uid,key):
        doc = self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$unset': {key: ''}}, projection={key: True})

        return from_db_fmt(doc.get(key))

    def increment(self,bucket_id,doc_uid,key,value=1):
        return self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$inc': {key: value}}, projection={key: True},
            new=True, upsert=True).get(key)

    def increment_many(self,bucket_id,doc_uid,key_value_dict):
        projection = {k: True for k in key_value_dict.keys()}
        values = {k: v for k, v in key_value_dict.items() if v != 0}

        new_doc = self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$inc': values}, projection=projection, new=True, upsert=True)

        return {k: new_doc.get(k) for k in key_value_dict.keys()}

    def get_list(self,bucket_id,doc_uid,key):
        return self.get(bucket_id, doc_uid, key)

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

    def append_list(self,bucket_id,doc_uid,key,value):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$push': {key: to_db_fmt(value)}}, upsert=True)

    def set_list(self,bucket_id,doc_uid,key,value):
        self.set(bucket_id, doc_uid, key, value)

    def set_doc(self,bucket_id,doc_uid,doc):
        if doc_uid is not None:
            doc['_id'] = doc_uid
        self._bucket(bucket_id).replace_one({"_id": doc_uid}, to_db_fmt(doc), upsert=True)

    def get_doc(self,bucket_id,doc_uid):
        return from_db_fmt(self._bucket(bucket_id).find_one({"_id": doc_uid}))

    def get_docs_with_filter(self,bucket_id,pattern_dict):
        docs_cursor = self._bucket(bucket_id).find(pattern_dict)

        return [from_db_fmt(doc) for doc in docs_cursor]

    def set(self,bucket_id,doc_uid,key,value):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$set': {key: to_db_fmt(value)}}, upsert=True)

    def set_many(self,bucket_id,doc_uid,key_value_dict):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$set': to_db_fmt(key_value_dict)})

    def delete(self,bucket_id,doc_uid,key):
        self._bucket(bucket_id).update_one({"_id": doc_uid},
            {'$unset': {key: True}})

    def ensure_index(self,bucket_id,index_dict):
        self._bucket(bucket_id).create_index(index_dict.items())

    def drop_all_indexes(self,bucket_id):
        self._bucket(bucket_id).drop_indexes()

    def delete_docs_with_filter(self,bucket_id,pattern_dict):
        docs,didSucceed,message = self.permStore.getDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)
        return self.permStore.deleteDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)

    def submit_job(self,app_id,exp_uid,task,task_args_json,namespace=None,ignore_result=True,time_limit=0, alg_id=None, alg_label=None):
        if self.broker is None:
            self.broker = next.broker.broker.JobBroker()
        if namespace is None:
            result = self.broker.applyAsync(app_id,exp_uid,task,task_args_json,ignore_result=ignore_result)
        else:
            result = self.broker.applySyncByNamespace(app_id,exp_uid,
                                                      alg_id, alg_label,
                                                      task,task_args_json,namespace=namespace,
                                                      ignore_result=ignore_result,time_limit=time_limit)
        return result

