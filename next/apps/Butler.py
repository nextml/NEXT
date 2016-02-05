from next.utils import utils

class Collection(object):
    def __init__(self, collection, uid_prefix, db, timing=True):
        self.collection = collection
        self.db = db
        self.uid_prefix = uid_prefix
        self.get_durations = 0.0
        self.set_durations = 0.0
        self.timing = timing
        
    def set(self, uid="", key=None, value=None):
        """
        Set an object in the collection, or an entry in an object in the collection.
        * key == None:    collection[uid] = value
        * key != None:    collection[uid][key] = value
        """
        uid = self.uid_prefix+uid
        if not key:
            self.timed(self.db.set_doc)(self.collection, uid, value)
        else:
            self.timed(self.db.set)(self.collection, uid, key, value)
        
    def get(self, uid="", key=None, pattern=None):
        """
        Get an object from the collection (possibly by pattern), or an entry (or entries) from an object in the collection.
        * key == None and pattern == None:                         return collection[uid]
        * key != None and pattern == None and type(key) != list:   return collection[uid][key]
        * key != None and pattern == None and type(key) == list:   return [collection[uid][k] for k in key]
        * pattern != None:                                         return collection[uid] matching pattern
        """
        uid = self.uid_prefix+uid
        if key==None and pattern==None:
            return self.timed(self.db.get_doc,get=True)(self.collection, uid)
        elif key:
            if(type(key) == list):
                return [self.timed(self.db.get,get=True)(self.collection, uid, k) for k in key]
            else:
                return self.timed(self.db.get,get=True)(self.collection, uid, key)
        else:
            return self.timed(self.db.get_docs_by_filter,get=True)(self.collection, pattern)

    def exists(self, uid=""):
        """
        Check if an object with the specified uid exists
        """
        uid = self.uid_prefix+uid
        return self.timed(self.db.exists,True)(self.collection, uid)

    def increment(self, uid="", key=None):
        """
        Increment a value (or values) in the collection.
        * type(key) != list:   increment collection[uid][key]
        * type(key) == list:   increment collection[uid][k] for k in key
        """
        uid = self.uid_prefix+uid
        if(type(key) == list):
            for k in key:
                self.timed(self.db.increment)(self.collection, uid, k)
        else:
            self.timed(self.db.increment)(self.collection, uid, key)

    def append(self, uid="", key=None, value=None):
        """
        Append a value to collection[uid][key] (which is assumed to be a list)
        """
        self.timed(self.db.append_list)(self.bucket_id,uid,key,value)
            
    def getDurations(self):
        """
        For book keeping purposes only
        """
        return {'duration_dbSet': self.duration_set, 'duration_dbGet' : self.duration_get}

    def timed(self, f, get=False):
        if not self.timing:
            return f
        
        def timed_f(*args, **kw):
            result,dt = utils.timeit(f)(*args, **kw)
            if(get):
                self.get_durations += dt
            else:
                self.set_durations += dt
            return result
        return timed_f
        
class Butler(object):
    def __init__(self, app_id, exp_uid, db, ell, alg_label=None, alg_id=None):
        self.app_id = app_id
        self.exp_uid = exp_uid
        self.alg_label = alg_label
        self.alg_id = alg_id
        self.db = db
        self.ell = ell
        self.queries = Collection(self.app_id+":queries", "", db)
        self.experiment = Collection(self.app_id+":experiments", self.exp_uid, db)
        self.algorithms = Collection(self.app_id+":algorithms", self.exp_uid+"_", db)
        self.participants = Collection(self.app_id+":participants", "", db)
        self.other = Collection(self.app_id+":other", self.exp_uid+"_", db)

    def log(self, log_name, log_value):
        self.ell.log(self.app_id+":"+log_name, log_value)
    

    def job(self,task,task_args_json,ignore_result=True,time_limit=0):
        if self.alg_label:
            self.db.submit_job(self.app_id, self.exp_uid,
                               task,
                               task_args_json,
                               self.exp_uid+'_'+self.alg_label,
                               ignore_result,
                               time_limit,
                               self.alg_id)  
        else:
            self.db.submit_job(self.app_id, self.exp_uid, task, task_args_json, None, ignore_result, time_limit)  

