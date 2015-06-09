import redis
import json
import numpy
from numpy import *

BUCKET_KEY = 'e%s:b%s:%s'               #
BUCKET_LIMIT = 500                      #
EXP_LENGTH = 'len:exp%s:%s'             # 
EXP_ID = 'expId'                        #

class Matrix:
    def __init__(self, expId, subId, embedding=None):
        self.conn = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.expId = expId
        self.subId = subId
        if embedding != None:
            self.save(self.expId, embedding)
    
    def save(self, expId, embedding):
        embedding = array(embedding, ndmin = 2)
        pipe = self.conn.pipeline()
        redis_key = '%s'
        length = len(embedding)
        
        if self.exists(expId, self.subId) and length < self.__len__(expId):
            print 'deleting'
            self.delete(expId, self.subId)
            
        for index in range(length):
            bucket = int(index / BUCKET_LIMIT)
            bucketKey = BUCKET_KEY % (expId, bucket, self.subId)
            val_dict = {'vector': embedding[index,:].tolist()}
            pipe.hset(bucketKey, redis_key % index, json.dumps(val_dict))
            index += 1
        pipe.set(EXP_LENGTH % (expId, self.subId), length)
        pipe.execute()
        
    def getEmbedding(self):
        pipe = self.conn.pipeline()                                             #
        blen = int(self.__len__()/BUCKET_LIMIT)                                 #
        results = []
 
        if blen == 0:
            blen = 1
        for i in range(blen):
            pipe.hvals(BUCKET_KEY % (self.expId, i, self.subId))
         
        items = pipe.execute()
         
        for i in range(len(items)):
            for j in range(len(items[i])):
                data  = json.loads(items[i][j])
                results.append(data['vector'])
        return results
    
    def append(self, value, expId = None, subId = None):
        if expId == None:
            expId = self.expId
        if subId == None:
            subId = self.subId

        embedding = array(value, ndmin = 2)
        pipe = self.conn.pipeline()
        redis_key = '%s'
        length = len(embedding)
        index = self.__len__(expId, subId)
        for i in range(length):
            bucket = int(index / BUCKET_LIMIT)
            bucketKey = BUCKET_KEY % (expId, bucket, subId)
            val_dict = {'vector': embedding[i,:].tolist()}
            pipe.hset(bucketKey, redis_key % index, json.dumps(val_dict))
            index += 1
        pipe.incrby(EXP_LENGTH % (expId, subId), length)
        pipe.execute() 
        
#     def append(self, value, expId = None):
#         if expId == None:
#             expId = self.expId
#         self.save(expId, value, self.__len__())

    def __getitem__(self, key):
        if isinstance(key, slice) :
            return [self[i] for i in xrange(*key.indices(len(self)))]
        elif isinstance(key, int) :
            if key < 0 :                                                        # Handle negative indices
                key += len(self)
                if key < 0:
                    raise IndexError, "The index (%d) is out of range." % key
            if key >= len( self ) :
                raise IndexError, "The index (%d) is out of range." % key
            return self._getRow(key)                                            # Get the data from elsewhere
        elif isinstance(key, list) or isinstance(key, numpy.ndarray):
            return self._getRows(key)
        else:
            raise TypeError, "Invalid argument type."
    
    def __setitem__(self, key, value):
        if isinstance(key, int) :
            if key < 0 :                                                        # Handle negative indices
                key += len(self)
                if key < 0:
                    raise IndexError, "The index (%d) is out of range." % key
            if key >= len( self ) :
                raise IndexError, "The index (%d) is out of range." % key
            return self._setRow(key, value)                                            # Get the data from elsewhere
        elif isinstance(key, list):
            print 'list'
            length = len(key)
#             if value.ndim == 1:
#                 value = value.reshape(length, value.shape[0]/length)
            if length != len(value):
                raise TypeError, "Invalid list."
            else:
                return self._setRows(key, value)
        else:
            raise TypeError, "Invalid argument type."
              
    def __len__(self, expId = None, subId = None):
        if expId == None:
            expId = self.expId
        if subId == None:
            subId = self.subId
        try:
            return int(self.conn.get(EXP_LENGTH % (expId, subId)))
        except:
            raise ValueError, "Experiment does not exist." % expId
        
    def _getRow(self, index):
        bucket = int(index / BUCKET_LIMIT)
        bucketKey = BUCKET_KEY % (self.expId, bucket, self.subId)
        items = self.conn.hget(bucketKey, index)
        data = json.loads(items)
        return data['vector']
    
    def _getRows(self, index):
        numargs = len(index)
        pipe = self.conn.pipeline()
        for i in range(numargs):
            if index[i] >= self.__len__() or index[i] < 0:
                raise IndexError, "The index (%d) is out of range." % index[i]
            bucket = int(index[i] / BUCKET_LIMIT)
            bucketKey = BUCKET_KEY % (self.expId, bucket, self.subId)
            pipe.hget(bucketKey, index[i])
        items = pipe.execute()
        results = []
        for i in range(numargs):
            data = json.loads(items[i])
            results.append(data['vector'])
        return results
    
    def _setRow(self, index, embedding):
        embedding = array(embedding, ndmin = 1)
        bucket = int(index / BUCKET_LIMIT)
        bucketKey = BUCKET_KEY % (self.expId, bucket, self.subId)
        redis_key = '%s'
        val_dict = {'vector': embedding.tolist()}
        self.conn.hset(bucketKey, redis_key % index, json.dumps(val_dict))
        
    def _setRows(self, indexes, rows):
        length = len(indexes)
        pipe = self.conn.pipeline()
        for i in range(length):
            if indexes[i] >= self.__len__() or indexes[i] < 0:
                raise IndexError, "The index (%d) is out of range." % indexes[i]
            bucket = int(indexes[i] / BUCKET_LIMIT)
            bucketKey = BUCKET_KEY % (self.expId, bucket, self.subId)
            redis_key = '%s'
            val_dict = {'vector': rows[i].tolist()}
            pipe.hset(bucketKey, redis_key % indexes[i], json.dumps(val_dict))
        pipe.execute()
        
    def delete(self, expId, subId):
        pipe = self.conn.pipeline()                                  # Create pipeline
        length = int(self.conn.get(EXP_LENGTH % (expId, subId)))     # Obtain current length
        length /= BUCKET_LIMIT                                       # Obtain buckets total
        
        for i in range(length+1):
            pipe.delete(BUCKET_KEY % (self.expId, i, subId))         # Delete each bucket
        pipe.delete(EXP_LENGTH % (expId, subId))                     # Delete length key
        pipe.execute()                                               # Execute commands in pipeline
       
    def exists(self, expId, subId):
        return self.conn.exists(EXP_LENGTH % (expId, subId))
    
    def getExpId(self):
        return self.expId
    
    def memory(self):
        return self.conn.info()['used_memory']
    
    # Only for testing purposes. Deletes all data on memory.
    def deleteAll(self):
        return self.conn.flushall()
        
#     def setExpId(self):
#         if self.conn.exists(EXP_ID):
#             self.expId = self.conn.incrby(EXP_ID, 1)
#             return self.expId
#         else:
#             self.expId = 0
#             self.conn.set(EXP_ID, 0)
#             return self.expId

#     def deleteFrom(self, expId, subId, start):
#         pipe = self.conn.pipeline()                                  # Create pipeline
# #         start /= BUCKET_LIMIT                                       # Obtain total of buckets
#         end = int(self.conn.get(EXP_LENGTH % (expId, subId)))     # Obtain current length
# #         end /= BUCKET_LIMIT                                       # Obtain total of buckets
#         
#         for i in range(start-1, end):
#             pipe.hdel(BUCKET_KEY % (self.expId, i/BUCKET_LIMIT, subId), i)         # Delete each bucket
#         pipe.set(EXP_LENGTH % (expId, subId), start)                     # Set hashes length to 0
#         pipe.execute()                                               # Execute commands in pipeline
