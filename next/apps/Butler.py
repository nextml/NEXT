class Collection(object):
    def __init__(self, collection, db):
        self.collection = collection
        self.db = db

    def set(self, uid, key=None, value=None, doc=None):
        return

    def get(self, uid, key=None, filter=None):
        return 
        
        
class Butler(object):
    def __init__(self, app_id, exp_uid, db, alg_label=None):
        self.app_id = app_id
        self.exp_uid = exp_uid
        self.alg_label = alg_label
        self.queries = Collection(self.app_id+":queries", db)
        self.experiments = Collection(self.app_id+":experiments", db)
        self.algorithms = Collection(self.app_id+":algorithms", db)
        self.participants = Collection(self.app_id+":participants", db)
        self.other = Collection(self.app_id+":other",db)

        
    
