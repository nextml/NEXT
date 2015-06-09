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
    from next.database.LoggerAPI import LoggerAPI
    ell = LoggerAPI()


"""

import next.constants as constants
import next.utils as utils
import next.database_client.PermStore.PermStore as PermStore

import cPickle

class LoggerAPI(object):
    """
    Serves as an API object that can be passed around. See above for usage

    Attributes:
        permStore : PermStore object
    """
    def __init__(self): 
        self.permStore = PermStore() 


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
        return self.permStore.setDoc(constants.logs_database_id,bucket_id,None,log_dict)

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
        didSucceed,message = self.permStore.create_index(constants.logs_database_id,bucket_id,index_dict)
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
        didSucceed,message = self.permStore.drop_all_indexes(constants.logs_database_id,bucket_id)
        return didSucceed,message

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
        permStoreConnected = self.permStore.assertConnection()
        if (permStoreConnected):
            return True,''
        else:
            return False,'no connection from Permstore'


    def irreversibly_delete_everything(self):
        self.permStore.deleteAll()


