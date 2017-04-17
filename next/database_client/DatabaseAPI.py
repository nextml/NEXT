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

import numpy as np
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.binary import Binary

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
        permStore : PermStore object
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

    def exists(self,bucket_id,doc_uid,key):
        """
        Checks existence of key.

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key

        Outputs:
            (bool) exists, (bool) didSucceed, (string) message

        Usage: ::\n
            exists,didSucceed,message = db.exists(bucket_id,doc_uid,key)
        """

        doc = self._bucket(bucket_id).find_one({"_id":doc_uid})
        return (doc != None)

    def get(self,bucket_id,doc_uid,key):
        """
        Get a value corresponding to key, returns None if no key exists

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key

        Outputs:
            (python object) value, (bool) didSucceed, (string) message

        Usage: ::\n
            value,didSucceed,message = db.get(bucket_id,doc_uid,key)
        """

        val = self._bucket(bucket_id).find_one({"_id": doc_uid}, {key: True}).get(key)
        return from_db_fmt(val)

    def get_many(self,bucket_id,doc_uid,key_list):
        """
        Get values corresponding to keys in key_list, returns None if no key exists

        Inputs:
            (string) bucket_id, (string) doc_uid, (list of string) key_list

        Outputs:
            (dict of {key1:value1,key2:value2}) return_dict, (bool) didSucceed, (string) message

        Usage: ::\n
            return_dict,didSucceed,message = db.get_many(bucket_id,doc_uid,key_list)
        """

        projection = {k: True for key in key_list}
        doc = self._bucket(bucket_id).find_one({"_id": doc_uid}, projection)
        val = {k: doc.get(k) for k in key_list}

        return from_db_fmt(val)

    def get_and_delete(self,bucket_id,doc_uid,key):
        """
        returns value associated with key and then deltes {key:value}. 
        If key does not exist, returns None
        
        Inputs: 
            (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs:
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.get_and_delete(bucket_id,doc_uid,key)
        """

        doc = self._bucket.find_one_and_update({"_id": doc_uid},
            update={'$unset': {key: ''}}, projection={key: True})

        return from_db_fmt(doc.get(key))

    def increment(self,bucket_id,doc_uid,key,value=1):
        """
        increments a key by amount value. If key does not exist, sets {key:value}

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key, (int) value

        Outputs:
            (int) new_value, (bool) didSucceed, (string) message

        Usage: ::\n
            new_value,didSucceed,message = db.increment(bucket_id,doc_uid,key,value)
        """

        return self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$inc': {key: value}}, projection={key: True},
            new=True, upsert=True).get(key)

    def increment_many(self,bucket_id,doc_uid,key_value_dict):
        """
        increments a key by amount value. If key does not exist, sets {key:value}

        Inputs:
            (string) bucket_id, (string) doc_uid, ({(str)key1:(float)value1,(int)key2:(float) value2}) key_value_dict

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.increment_many(bucket_id,doc_uid,key_value_dict)
        """
        projection = {k: True for k in key_value_dict.keys()}
        values = {k: v for k, v in key_value_dict.items() if v != 0}

        new_doc = self._bucket(bucket_id).find_one_and_update({"_id": doc_uid},
            update={'$inc': values}, projection=projection, new=true, upsert=true)

        return {k: new_doc.get(k) for k in key_value_dict.keys()}

    def get_list(self,bucket_id,doc_uid,key):
        """
        Get a value corresponding to key, returns None if no key exists

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key

        Outputs:
            (list) value, (bool) didSucceed, (string) message

        Usage: ::\n
            value,didSucceed,message = db.get_list(bucket_id,doc_uid,key)
        """
        return self.get(bucket_id, doc_uid, key)

    def pop_list(self, bucket_id, doc_uid, key, value):
        """
        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key, (int) value
            value=-1 pops the last item of the list
            value=0 pops the first item of the list

        Outputs:
            (python object) value, (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.pop_list(bucket_id,doc_uid,key,value)       
        """

        try:
            response, dt = utils.timeit(self.permStore.pop_list)(constants.app_data_database_id,
                                                                 bucket_id, doc_uid, key, value)
            value, didSucceedPerm, messagePerm = response
            self.duration_permStoreSet += dt
            return value, didSucceedPerm, messagePerm
        except Exception as e:
            error = "DatabaseAPI.pop_list failed with exception: {}".format(e)
            utils.debug_print(error)
            return None, False, error

    def append_list(self,bucket_id,doc_uid,key,value):
        """
        Appends a {key,value_list} (if already exists, replaces)

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key, (list) value

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.set_list(bucket_id,doc_uid,key,value)
        """

        try:
            response,dt = utils.timeit(self.permStore.append_list)(constants.app_data_database_id,bucket_id,doc_uid,key,value)
            didSucceedPerm,messagePerm = response
            self.duration_permStoreSet += dt
            return didSucceedPerm,messagePerm
        except:
            error = "DatabaseAPI.append_list Failed with unknown exception"
            return False,error

    def set_list(self,bucket_id,doc_uid,key,value):
        """
        Sets a {key,value_list} (if already exists, replaces)

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key, (list) value

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.set_list(bucket_id,doc_uid,key,value)
        """
        try:
            response,dt = utils.timeit(self.permStore.set_list)(constants.app_data_database_id,bucket_id,doc_uid,key,value)
            didSucceedPerm,messagePerm = response
            self.duration_permStoreSet += dt
            return didSucceedPerm,messagePerm
        except:
            error = "DatabaseAPI.set Failed with unknown exception"
            return False,error

    def set_doc(self,bucket_id,doc_uid,doc):
        """
        Sets a document with doc_uid

        Inputs:
            (dict) doc

        Outputs:
            None

        Usage: ::\n
            db.set_doc(key,value)
        """
        didSucceed,message = self.permStore.setDoc(constants.app_data_database_id,bucket_id,doc_uid,doc)
        return didSucceed,message

    def get_doc(self,bucket_id,doc_uid):
        """
        Gets doc in bucket_id that corresponds to doc_uid

        Inputs:
            (string) bucket_id, (string) doc_uid

        Outputs:
            (dict) doc, (bool) didSucceed, (string) message

        Usage: ::\n
            doc,didSucceed,message = db.getDoc(bucket_id,doc_uid)
        """
        return self.permStore.getDoc(constants.app_data_database_id,bucket_id,doc_uid)

    def get_docs_with_filter(self,bucket_id,pattern_dict):
        """
        Retrieves all docs in bucket_id that match (i.e. contain) pattern_dict

        Inputs:
            (string) bucket_id, (dict of string values) pattern_dict

        Outputs:
            (list of dict) docs, (bool) didSucceed, (string) message

        Usage: ::\n
            docs,didSucceed,message = db.getDocsByPattern(bucket_id,pattern_dict)
        """
        t = self.permStore.getDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)
        return t

    def set(self,bucket_id,doc_uid,key,value):
        """
        Sets a {key,value} (if already exists, replaces)

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key, (string) value

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.set(bucket_id,doc_uid,key,value)
        """
        try:
            response,dt = utils.timeit(self.permStore.set)(constants.app_data_database_id,bucket_id,doc_uid,key,value)
            didSucceedPerm,messagePerm = response
            self.duration_permStoreSet += dt
            return didSucceedPerm,messagePerm
        except:
            error = "DatabaseAPI.set Failed with unknown exception"
            return False,error

    def set_many(self,bucket_id,doc_uid,key_value_dict):
        """
        sets key, values in dict. If key does not exist, sets {key:value}

        Inputs:
            (string) bucket_id, (string) doc_uid, ({(str)key1:(float)value1,(int)key2:(float) value2}) key_value_dict

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.set_many(bucket_id,doc_uid,key_value_dict)
        """
        try:
            response,dt = utils.timeit(self.permStore.set_many)(constants.app_data_database_id,bucket_id,doc_uid,key_value_dict)
            didSucceed,message = response
            self.duration_permStoreSet += dt
            if not didSucceed:
                return False,message
            return True,'Hit PermStore'

        except:
            return None,False,'DatabaseAPI.set_many Failed with unknown exception'


    def delete(self,bucket_id,doc_uid,key):
        """
        Deletes {key:value} associated with given key

        Inputs:
            (string) bucket_id, (string) doc_uid, (string) key

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.delete(bucket_id,doc_uid,key)
        """
        try:
            didSucceed,message = self.permStore.delete(constants.app_data_database_id,bucket_id,doc_uid,key)
            return didSucceed,message
        except:
            error = "DatabaseAPI.delete Failed with unknown exception"
            return False,error

    def ensure_index(self,bucket_id,index_dict):
        """
        Adds index defined on index_dict to bucket_id

        Inputs:
            (string) bucket_id, (dict) index_dict

        Outputs:
            (string) index_info, (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.get_index_info('rand_data',{'num_eyes':1,'exp_uid',1})
        """
        didSucceed,message = self.permStore.create_index(constants.app_data_database_id,bucket_id,index_dict)
        return didSucceed,message

    def drop_all_indexes(self,bucket_id):
        """
        Deletes all indexes defined on bucket_id

        Inputs:
            (string) bucket_id

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.drop_all_indexes(bucket_id)
        """
        didSucceed,message = self.permStore.drop_all_indexes(constants.app_data_database_id,bucket_id)
        return didSucceed,message

    def delete_docs_with_filter(self,bucket_id,pattern_dict):
        """
        Deletes all docs in bucket_id that match (i.e. contain) pattern_dict

        Inputs:
            (string) bucket_id, (dict of string values) pattern_dict

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.deleteDocsByPattern(bucket_id,key,value)
        """
        docs,didSucceed,message = self.permStore.getDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)
        return self.permStore.deleteDocsByPattern(constants.app_data_database_id,bucket_id,pattern_dict)

    def log(self,bucket_id,log_dict):
        """
        Saves log_dict to PermStore as an individual document for later recall.

        Inputs:
            (string) bucket_id, (dict with string values) log_dict

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.log(bucket_id,doc_uid)
        """
        timestamp = utils.datetimeNow()
        log_dict.update({ 'timestamp':timestamp })
        return self.permStore.setDoc(constants.logs_database_id,bucket_id,None,log_dict)

    def get_logs_with_filter(self,bucket_id,pattern_dict):
        """
        Retrieves all logs in bucket_id that match (i.e. contain) pattern_dict

        Inputs:
            (string) bucket_id, (dict of string values) pattern_dict

        Outputs:
            (list of dict) logs, (bool) didSucceed, (string) message

        Usage: ::\n
            logs,didSucceed,message = db.getLogsByPattern(bucket_id,pattern_dict)
        """
        return self.permStore.getDocsByPattern(constants.logs_database_id,bucket_id,pattern_dict)

    def delete_logs_with_filter(self,bucket_id,pattern_dict):
        """
        Deletes all logs in bucket_id that match (i.e. contain) pattern_dict

        Inputs:
            (string) bucket_id, (dict of string values) pattern_dict

        Outputs:
            (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.deleteLogsByPattern(bucket_id,key,value)
        """
        return self.permStore.deleteDocsByPattern(constants.logs_database_id,bucket_id,pattern_dict)


    def assertConnection(self):
        """
        Asserts that the API has successfully connected to the PermStore

        Inputs:
            None

        Outputs:
            (bool) areConnected, (string) message

        Usage: ::\n
            didSucceed,message = db.assertConnection()
        """
        try:
            permStoreConnected = self.permStore.assertConnection()
            if (permStoreConnected):
                return True,'Established PermStore connection'
            else:
                return False,'No connection from PermStore'
        except:
            error = "DatabaseAPI.assertConnection unknown exception"
            return False, error

    def getDocNames(self,bucket_id):
        """
        Get list of doc_uids correspding to all the docs in the bucket corresponding to the given bucket_id

        Inputs:
            (string) bucket_id

        Outputs:
            ([(string) doc_uid, ... ]) docNames, (bool) didSucceed, (string) message

        Usage: ::\n
            docNames,didSucceed,message = db.getDocNames(bucket_id)
        """
        try:
            doc_uids,didSucceed,message = self.permStore.getDocNames(constants.app_data_database_id,bucket_id)
            if not didSucceed:
                return None,False,message

            return doc_uids,True,''
        except:
            error = "DatabaseAPI.getDocNames Failed with unknown exception"
            return None,False,error

    def getBucketNames(self):
        """
        Get list of bucket_ids

        Inputs:
            None

        Outputs:
            ([(string) bucket_id, ... ]) bucketNames, (bool) didSucceed, (string) message

        Usage: ::\n
            bucketNames,didSucceed,message = db.getBucketNames()
        """
        try:
            bucket_ids,didSucceed,message = self.permStore.getBucketNames(constants.app_data_database_id)
            if not didSucceed:
                return None,False,message

            return bucket_ids,True,''
        except:
            error = "DatabaseAPI.getDocNames Failed with unknown exception"
            return None,False,error


    def inspectDatabase(self):
        """
        Returns string describing the entire app data database

        Inputs:
            None

        Outputs:
            (string) description, (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.inspectDatabase()
        """
        try:
            output_str = ''
            bucket_ids,didSucceed,message = self.permStore.getBucketNames(constants.app_data_database_id)
            for bucket_id in bucket_ids:
                bucket_id_str = str(bucket_id)
                output_str += bucket_id_str + " { \n"
                doc_uids,didSucceed,message = self.permStore.getDocNames(constants.app_data_database_id,bucket_id)
                if doc_uids!=None :
                    for doc_uid in doc_uids:
                        doc_uid_str = str(doc_uid)
                        output_str += "\t" + doc_uid_str + " { \n"
                        doc,didSucceed,message = self.permStore.getDoc(constants.app_data_database_id,bucket_id,doc_uid)
                        for key in doc:
                            pickled_value = doc[key]
                            try:
                                value = cPickle.loads(pickled_value)
                            except:
                                value = pickled_value
                            str_value = str(value)
                            if len(str_value)>constants.maxStringLengthInInspectDatabase:
                                str_value = str_value[0:constants.maxStringLengthInInspectDatabase]+ " ..."
                            output_str += "\t\t" + key + " : " + str_value + "\n"
                    output_str += "\t" + "}" + "\n"
            output_str += "}" + "\n"
            return output_str,True,''
        except:
            error = "DatabaseAPI.inspectDatabase() incurred an unknown exception "
            return None,False,error



    def inspectDoc(self,bucket_id,doc_uid):
        """
        Returns string describing the document of the particular bucket_id, doc_uid

        Inputs:
            (string) bucket_id, (string) doc_uid

        Outputs:
            (string) description, (bool) didSucceed, (string) message

        Usage: ::\n
            didSucceed,message = db.inspectDatabase()
        """
        try:
            output_str = ''
            output_str += doc_uid + " { \n"
            doc,didSucceed,message = self.permStore.getDoc(constants.app_data_database_id,bucket_id,doc_uid)
            for key in doc:
                pickled_value = doc[key]
                try:
                    value = cPickle.loads(pickled_value)
                except:
                    value = pickled_value
                str_value = str(value)
                if len(str_value)>constants.maxStringLengthInInspectDatabase:
                    str_value = str_value[0:max_value_string_length]+ " ..."
                output_str += "\t" + key + " : " + str_value + "\n"
            output_str += "}" + "\n"

            return output_str,True,''
        except:
            return None,False,'DatabaseAPI.inspectDoc unknown exception'

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

