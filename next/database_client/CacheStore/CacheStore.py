"""
Cache Store
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 12/31/2014

Cache in-memory storage solution. Database hierarchy is organized as:
CacheStore[database_id][bucket_id][doc_uid] = {key1:value1,key2:value2,...}

The database assumes that only string values are stored (even though other values may work)

Initialization::\n
    db = CacheStore()

Database functions::\n 
    exists,didSucceed,message = db.exists(database_id,bucket_id,doc_uid,key)

    value,didSucceed,message = db.get(database_id,bucket_id,doc_uid,key)

    didSucceed,message = db.set(database_id,bucket_id,doc_uid,key)
    didSucceed,message = db.setDoc(database_id,bucket_id,doc_uid,doc)

    didSucceed,message = db.delete(database_id,bucket_id,doc_uid,key)
    didSucceed,message = db.deleteDoc(database_id,bucket_id,doc_uid)
    didSucceed,message = db.deleteBucket(database_id,bucket_id)
    didSucceed,message = db.deleteDatabase(database_id)
    didSucceed,message = db.deleteAll()

Database inspection ::\n
    docNames,didSucceed,message = db.getDocNames(database_id,bucket_id)
    bucketNames,didSucceed,message = db.getBucketNames(database_id)
    databaseNames,didSucceed,message = db.getDatabaseNames()
"""

import redis
import next.constants as constants
import cPickle

class CacheStore(object):
    """
    Acts as API to cache store that can be passed around. Implements Redis

    Attribtues:
        client : Redis client
    """

    def __init__(self): 
        # self.r = redis.StrictRedis(host=constants.MINIONREDIS_HOST, port=constants.MINIONREDIS_PORT, password=constants.MINIONREDIS_PASS)
        self.r = redis.StrictRedis(host=constants.MINIONREDIS_HOST, port=constants.MINIONREDIS_PORT)

    def assertConnection(self):
        """ 
        Checks that Redis is running

        Inputs:
            None

        Outputs:
            (boolean) isConnected

        Usage: ::\n
            db.assertConnection()
        """
        try:
            return self.r.ping()
        except:
            raise
            return False

    def getRedisKey(self,database_id,bucket_id,doc_uid,key):
        """
        Redis is a key-value store so we convert database_id,budget_id,etc. to a single unique string

        Inputs:
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key

        Outputs
            (string) redis_key

        Usage: ::\n
            redisKey = db.getRedisKey(database_id,bucket_id,doc_uid,key)
        """
        return database_id+":"+bucket_id+":"+doc_uid+":"+key


    def exists(self,database_id,bucket_id,doc_uid,key):
        """
        check existence of key
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs: 
            (bool) exists, (bool) didSucceed, (string) message 
        
        Usage: ::\n 
            exists,didSucceed,message = db.exists(database_id,bucket_id,doc_uid,key)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            key_exists = self.r.exists(redis_key)

            return key_exists,True,''
        except:
            error = "Redis.exists Failed with unknown exception"
            return False,False,error

    def get(self,database_id,bucket_id,doc_uid,key):
        """
        get a value corresponding to key, returns None if no key exists
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs: 
            (string) value, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            value,didSucceed,message = db.get(database_id,bucket_id,doc_uid,key)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            value = self.r.get(redis_key)

            try:
                return_value = cPickle.loads(value)
            except:
                return_value = value

            return return_value,True,'From Redis'

        except:
            return None,False,'Redis.get Failed with unknown exception'

    def increment(self,database_id,bucket_id,doc_uid,key,value):
        """
        increments a key by amount value. If key does not exist, sets {key:value}

        WARNING: This will return an int, but if you 'get' this value, a string may be returned so always cast it as an int.
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key, (int) value
        
        Outputs:
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            new_value,didSucceed,message = db.set(database_id,bucket_id,doc_uid,key,value)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            new_value = self.r.incr(redis_key,value)

            return new_value,True,'From Redis'
        except:
            return None,False,'Redis.increment Failed with unknown exception'

    def get_list(self,database_id,bucket_id,doc_uid,key):
        """
        gets saved by key. If key does not exist, returns None
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs:
            (list) list_value, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.get_list(database_id,bucket_id,doc_uid,key,value)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            list_value = self.r.lrange(redis_key,0,-1)

            new_list_value = []
            for value in list_value:
                try:
                    new_list_value.append( cPickle.loads(value) )
                except:
                    new_list_value.append( value )

            return new_list_value,True,'From Redis'
        except:
            error = "Redis.get_list Failed with unknown exception"
            return False,error

    def append_list(self,database_id,bucket_id,doc_uid,key,value):
        """
        appends value to list saved by key. If key does not exist, sets {key:value}
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key, (int) value
        
        Outputs:
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.set(database_id,bucket_id,doc_uid,key,value)
        """
        try:
            if type(value)!=str:
                # pickle value so we can handle any python type
                value = cPickle.dumps(value, protocol=2)

            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            self.r.rpush(redis_key,value)

            return True,'To Redis'
        except:
            error = "Redis.append_list Failed with unknown exception"
            return False,error

    def set_list(self,database_id,bucket_id,doc_uid,key,value_list):
        """
        sets a list to {key,value_list} (if already exists, replaces)
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key, (list) value_list
        
        Outputs:
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.set_list(database_id,bucket_id,doc_uid,key,value)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            pipe = self.r.pipeline()
            pipe.delete(redis_key)
            for value in value_list:
                if type(value)!=str:
                    # pickle value so we can handle any python type
                    value = cPickle.dumps(value, protocol=2)
                pipe.rpush(redis_key,value)
            returns = pipe.execute()

            return True,'To Redis'
        except:
            error = "Redis.get_list Failed with unknown exception"
            return False,error

    def set(self,database_id,bucket_id,doc_uid,key,value):
        """
        sets a {key,value} (if already exists, replaces)
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key, (string) value
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.set(database_id,bucket_id,doc_uid,key,value)
        """
        try:
            if type(value)!=str:
                # pickle value so we can handle any python type
                value = cPickle.dumps(value, protocol=2)

            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            didSucceed = self.r.set(redis_key,value)

            if didSucceed:
                return True,'Redis.set Succeeded'
            else:
                return False,'Redis.set Failed'
        except:
            error = "Redis.set Failed with unknown exception"
            return False,error

    def setDoc(self,database_id,bucket_id,doc_uid,doc):
        """
        set a doc (dictionary of string values) 
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, ({ (string) key: (string) value, ... }) doc
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.setDoc(database_id,bucket_id,doc_uid,key,value)
        """
        try:
            for key in doc:
                didSucceed,message = self.set(database_id,bucket_id,doc_uid,key,doc[key])
                if not didSucceed:
                    return False,'Redis.set Failed'
            return True,'Redis.set Succeeded'
        except:
            error = "Redis.set Failed with unknown exception"
            return False,error

    def delete(self,database_id,bucket_id,doc_uid,key):
        """
        deletes {key:value} associated with given key
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.delete(database_id,bucket_id,doc_uid,key)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,key)

            key_exists = self.r.exists(redis_key)
            if key_exists:
                numKeysDeleted = self.r.delete(redis_key)
                if numKeysDeleted==1:
                    return True,''
                else:
                    return False,'Redis.delete key exists but failed to be deleted'
            else:
                return True,'Redis.delete key does not exist'
        except:
            error = "Redis.delete Failed with unknown exception"
            return False,error

    def deleteDoc(self,database_id,bucket_id,doc_uid):
        """
        deletes doc associated with given doc_uid
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.deleteDoc(database_id,bucket_id,doc_uid)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,doc_uid,'*')

            for child_redis_key in self.r.keys(redis_key):
                numKeysDeleted = self.r.delete(child_redis_key)

            return True,''
        except:
            error = "Redis.deleteDoc Failed with unknown exception"
            return False,error

    def deleteBucket(self,database_id,bucket_id):
        """
        deletes bucket (and all docs in it) associated with given bucket_id
        
        Inputs: 
            (string) database_id, (string) bucket_id
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.deleteBucket(database_id,bucket_id)
        """
        try:
            redis_key = self.getRedisKey(database_id,bucket_id,'*','*')

            for child_redis_key in self.r.keys(redis_key):
                numKeysDeleted = self.r.delete(child_redis_key)

            return True,''
        except:
            error = "Redis.deleteBucket Failed with unknown exception"
            return False,error

    def deleteDatabase(self,database_id):
        """
        deletes database (and all docs in it) associated with given bucket_id
        
        Inputs: 
            (string) database_id
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.deleteDatabase(database_id)
        """
        try:
            redis_key = self.getRedisKey(database_id,'*','*','*')

            for child_redis_key in self.r.keys(redis_key):
                numKeysDeleted = self.r.delete(child_redis_key)

            return True,''
        except:
            error = "Redis.deleteDoc Failed with unknown exception"
            return False,error

    def deleteAll(self):
        """
        deletes everything in cache
        
        Inputs: 
            None
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.deleteAll()
        """
        try:
            self.r.flushall()

            return True,''
        except:
            error = "Redis.flush_all Failed with unknown exception"
            return False,error




