import redis
from itertools import chain

DICT_KEY = 'exp%s:%s'                 # Hash key for a matrixOriginal
DICT_KEYS = 'exp%s:%s:keys'           # Hash key for a matrixOriginal

class Dictionary:
    def __init__(self, expId, subId, dictionary=None):
        self.conn = redis.StrictRedis(host='localhost',         # Open Redis connection
                                      port=6379, db=0)
        self.expId = expId
        self.subId = subId
        if dictionary is not None:
            self.save(self.expId, dictionary)                   # If a  dictionary is provided, it is stored in Redis 
    
    def save(self, expId, dictionary):
        if isinstance(dictionary, dict):
            dictKey = DICT_KEY % (expId, self.subId)
            pipe = self.conn.pipeline()                                         # Initialize pipeline        
            for key in dictionary:
                pipe.hset(dictKey, key, dictionary[key])
            pipe.execute()                                                      # Execute commands on pipeline
        else:
            raise TypeError, "Invalid argument type."
    
    def getDictionary(self): 
        return self.conn.hgetall(DICT_KEY % (self.expId, self.subId))
    
    def _getValue(self, key):
        dictKey = DICT_KEY % (self.expId, self.subId)
        if self.has_key(self.expId, self.subId, key):
            return self.conn.hget(dictKey, key)
        else:
            raise KeyError, "Key does not exists: %s" % key
    
    def _getValues(self, keys):
        dictKey = DICT_KEY % (self.expId, self.subId)
        if self.has_key(self.expId, self.subId, keys):
            return self.conn.hmget(dictKey, *keys)
        else:
            raise KeyError, "Key does not exists: %s" % str(keys)      

    def _setValue(self, key, value):
        dictKey = DICT_KEY % (self.expId, self.subId)
        return self.conn.hset(dictKey, key, value)

    def _setValues(self, keys, values):
        if len(keys) != len(values):
            raise TypeError
        dictKey = DICT_KEY % (self.expId, self.subId)
        fields = list(chain(*zip(keys,values)))
        return self.conn.hmset(dictKey, dict(zip(*[iter(fields)]*2)))
    
    def get(self, key, default = None):
        dictKey = DICT_KEY % (self.expId, self.subId)
        if self.has_key(self.expId, self.subId, key):
            return self.conn.hget(dictKey, key)
        else:
            return default
    
    def clear(self):
        return self.delete()
        
    def delete(self):
        self.conn.delete(DICT_KEY % (self.expId, self.subId))
                  
    def __getitem__(self, key):
        if isinstance(key, (str, int, long, float, bool, tuple)):
            return self._getValue(key)
        elif isinstance(key, tuple):
            return self._getValues(key)
        else:
            raise TypeError, "Invalid argument type: %s" % type(key).__name__

    def __setitem__(self, key, value):
        if isinstance(key, list):
            length = len(key)
            for i in range(length): 
                if isinstance(key[i], (str, int, long, float, bool)):
                    continue
                else:
                    raise TypeError
            return self._setValues(key, value)
        elif isinstance(key, (str, tuple, int, long, float, bool)):
                return self._setValue(key, value)
        else:
            raise TypeError
              
    def __len__(self, expId = None, subId = None):
        if expId is None:
            expId = self.expId
        if subId is None:
            subId = self.subId
        try:
            return int(self.conn.hlen(DICT_KEY % (expId, subId)))
        except:
            raise ValueError, "Experiment does not exist." % expId
         
#     def __del__(self):
# #         self.conn.delete(DICT_KEY % (self.expId, self.subId))
#         print self.expId, 'died'
        
    def __delitem__(self, key):
        if self.has_key(self.expId, self.subId, key):
            print 'exist'
            if isinstance(key, tuple):
                print 'Del tuple'
                self.conn.hdel(DICT_KEY % (self.expId, self.subId), *key)
            else:
                self.conn.hdel(DICT_KEY % (self.expId, self.subId), key)
        else:
            raise KeyError, "Key does not exists: %s" % str(key)
    
    def has_key(self, expId, subId, keys):
        dictKey = DICT_KEY % (expId, subId)
        if isinstance(keys, tuple) or isinstance(keys, list):
            length = len(keys)
            for i in range(length):
                if not self.conn.hexists(dictKey, keys[i]):
                    return False
            return True
        else:
            if not self.conn.hexists(dictKey, keys):
                return False
            return True

    def fromkeys(self, keys, value=None):
        d = {}
        for key in keys:
            d[key] = value
        return d
             
    def memory(self):
        return self.conn.info()['used_memory']
    
    def deleteAll(self):
        return self.conn.flushall()
    
    def __iter__(self):
        return DictIter(self)
    
    def itervalues(self):
        return DictIter(self, 'values')
     
    def iterkeys(self):
        return DictIter(self, 'keys')
        
    def iteritems(self):
        return DictIter(self, 'items')
    
    def keys(self):
        dictKey = DICT_KEY % (self.expId, self.subId)
        return self.conn.hkeys(dictKey)
    
    def values(self):
        dictKey = DICT_KEY % (self.expId, self.subId)
        return self.conn.hvalues(dictKey)  
    
    def __repr__(self):
        r = ["{0!r} : {1!r}".format(k, v) for k, v in self.iteritems()]
        return "Dict({" + ", ".join(r) + "})"
    
class DictIter(object):
    def __init__(self, dictionary, kind=None):
        self.kind = kind
        self.dictKey = DICT_KEY % (dictionary.expId, dictionary.subId)
        self.keys = dictionary.conn.hkeys(self.dictKey)
        self.dictionary = dictionary
        self.i = -1
        
    def __iter__(self):
        return self
    
    def next(self):
        if self.i < self.dictionary.__len__()-1:
            self.i += 1
            if (self.kind == 'keys'):
                return self.keys[self.i]
            elif (self.kind == 'values'):
                return self.dictionary._getValue(self.keys[self.i])
            elif (self.kind == 'items'):
                return self.keys[self.i], self.dictionary._getValue(self.keys[self.i])
            else:
                return self.keys[self.i]
        else:
            raise StopIteration