from next.utils import utils

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
        
    def get(self, uid="", key=None, pattern=None, exp=None):
        """
        Get an object from the collection (possibly by pattern), or an entry (or entries) from an object in the collection.
        * key == None and pattern == None:                         return collection[uid]
        * key != None and pattern == None and type(key) != list:   return collection[uid][key]
        * key != None and pattern == None and type(key) == list:   return [collection[uid][k] for k in key]
        * pattern != None:                                         return collection[uid] matching pattern
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        if key==None and pattern==None:
            return self.timed(self.db.get_doc, get=True)(self.collection, uid)
        elif key:
            if(type(key) == list):
                return [self.timed(self.db.get, get=True)(self.collection, uid, k) for k in key]
            else:
                return self.timed(self.db.get, get=True)(self.collection, uid, key)
        else:
            return self.timed(self.db.get_docs_by_filter, get=True)(self.collection, pattern)

    def exists(self, uid="", key='_id', exp=None):
        """
        Check if an object with the specified uid exists
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        result = self.timed(self.db.exists, get=True)(self.collection, uid, key)
        print "Butler.py:exist, exist check", uid, key, result
        return result#self.timed(self.db.exists,get=True)(self.collection, uid, key)

    def increment(self, uid="", key=None, exp=None, value=1.0):
        """
        Increment a value (or values) in the collection.
        * type(key) != list:   increment collection[uid][key]
        * type(key) == list:   increment collection[uid][k] for k in key

        * values: How much the value should be incremented by.
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        if(type(key) == list):
            if type(value) in {int, float}:
                value = len(key)*[value]
            for k, v in zip(key, value):
                self.timed(self.db.increment, get=True)(self.collection, uid, k, v)
        else:
            if value == None:
                value = 1
            return self.timed(self.db.increment, get=True)(self.collection, uid, key, value)

    def append(self, uid="", key=None, value=None, exp=None):
        """
        Append a value to collection[uid][key] (which is assumed to be a list)
        """
        uid = (self.uid_prefix+uid).format(exp_uid=(self.exp_uid if exp == None else exp))
        self.timed(self.db.append_list)(self.collection,uid,key,value)
            
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
        self.queries = Collection(self.app_id+":queries", "", self.exp_uid, db)
        self.experiment = Collection(self.app_id+":experiments", "{exp_uid}", self.exp_uid, db)
        if alg_label is None:
            self.algorithms = Collection(self.app_id+":algorithms", "{exp_uid}_", self.exp_uid, db)
        else:
            self.algorithms = Collection(self.app_id+":algorithms", "{exp_uid}_"+alg_label, self.exp_uid, db)
        self.participants = Collection(self.app_id+":participants", "", self.exp_uid, db)
        self.other = Collection(self.app_id+":other", "{exp_uid}_", self.exp_uid, db)

    def log(self, log_name, log_value):
        self.ell.log(self.app_id+":"+log_name, log_value)
    

    def job(self,task,task_args_json,ignore_result=True,time_limit=0):
        if self.alg_label:
            print "butler job", self.app_id, self.exp_uid, self.alg_label, self.alg_id, task
            self.db.submit_job(self.app_id,self.exp_uid,
                               task,task_args_json,self.targets,
                               self.exp_uid+'_'+self.alg_label,
                               ignore_result,time_limit,
                               alg_id = self.alg_id, alg_label=self.alg_label)  
        else:
            self.db.submit_job(self.app_id, self.exp_uid, task, task_args_json, self.targets, None, ignore_result, time_limit)  

