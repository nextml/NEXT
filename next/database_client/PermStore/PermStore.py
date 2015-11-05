"""
Perm Store
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 12/31/2014

Persistent storage solution. Database hierarchy is organized as: ::\n
    PermStore[database_id][bucket_id][doc_uid] = {key1:value1,key2:value2,...}

Dependencies: next.constants to determine location of mongoDB server

Some common functions
###############################

Initialization::\n
    db = PermStore()

Database functions::\n 
    exists,didSucceed,message = db.exists(database_id,bucket_id,doc_uid,key)

    value,didSucceed,message = db.get(database_id,bucket_id,doc_uid,key)
    doc,didSucceed,message = db.getDoc(database_id,bucket_id,doc_uid)
    docs,didSucceed,message = db.getDocsByPattern(database_id,bucket_id,filter_dict)

    didSucceed,message = db.set(database_id,bucket_id,doc_uid,key,value)
    didSucceed,message = db.setDoc(database_id,bucket_id,doc_uid,doc)

    didSucceed,message = db.delete(database_id,bucket_id,doc_uid,key)
    didSucceed,message = db.deleteDoc(database_id,bucket_id,doc_uid)
    didSucceed,message = db.deleteDocsByPattern(database_id,bucket_id,filter_dict)
    didSucceed,message = db.deleteBucket(database_id,bucket_id)
    didSucceed,message = db.deleteDatabase(database_id)
    didSucceed,message = db.deleteAll()

Database inspection ::\n
    docNames,didSucceed,message = db.getDocNames(database_id,bucket_id)
    bucketNames,didSucceed,message = db.getBucketNames(database_id)
    databaseNames,didSucceed,message = db.getDatabaseNames()

Some example usage
###############################

Let's first inititlize the database ::\n
    from next.database.PermStore import PermStore
    db = PermStore()

And let's assume that the database is empty, which we can enforce by deleting everything ::\n
    didSucceed,message = db.deleteAll()

Building up a document one key at a time ::\n
    database_id = 'things'
    bucket_id = 'animals'

    doc_uid = 'cat'

    didSucceed,message = db.set(database_id,bucket_id,doc_uid,'color','black')
    didSucceed,message = db.set(database_id,bucket_id,doc_uid,'num_legs',4)
    didSucceed,message = db.set(database_id,bucket_id,doc_uid,'age',7.5)
    
Inserting a document ::\n
    database_id = 'things'
    bucket_id = 'animals'

    doc_uid = 'dog'
    doc = {'color':'brown','num_legs':4,'age':9.5}
    didSucceed,message = db.setDoc(database_id,bucket_id,doc_uid,doc)

    doc_uid = 'human'
    doc = {'color':'tan','num_legs':2,'age':28}
    didSucceed,message = db.setDoc(database_id,bucket_id,doc_uid,doc)
    
Retrieving values ::\n
    value,didSucceed,message = db.get('things','animals','dog','age')
    print value
    >>> 9.5
        
Retrieving docs ::\n
    doc,didSucceed,message = db.getDoc('things','animals','cat')
    print doc
    >>> {u'color': u'black', u'age': 7.5, u'_id': u'cat', u'num_legs': 4}

    doc,didSucceed,message = db.getDoc('things','animals','dog')
    print doc
    >>> {u'color': u'brown', u'age': 9.5, u'_id': u'dog', u'num_legs': 4}
    
Advanced doc retrieval ::\n
    docs,didSucceed,message = db.getDocsByPattern('things','animals',{})
    print docs
        >>> [{u'color': u'black', u'age': 7.5, u'_id': 'cat', u'num_legs': 4}, {u'color': u'brown', u'age': 9.5, u'_id': 'dog', u'num_legs': 4}, {u'color': u'tan', u'age': 28, u'_id': 'human', u'num_legs': 2}]

    docs,didSucceed,message = db.getDocsByPattern('things','animals',{'num_legs':4})
        >>> [{u'color': u'black', u'age': 7.5, u'_id': 'cat', u'num_legs': 4}, {u'color': u'brown', u'age': 9.5, u'_id': 'dog', u'num_legs': 4}]


    docs,didSucceed,message = db.getDocsByPattern('things','animals',{'age':{ '$gte':8,'$lt':10} })
        >>> [{u'color': u'brown', u'age': 9.5, u'_id': 'dog', u'num_legs': 4}]


    docs,didSucceed,message = db.getDocsByPattern('things','animals',{'age':{ '$gte':8 }, 'num_legs':2 })
        >>> [{u'color': u'tan', u'age': 28, u'_id': 'human', u'num_legs': 2}]
    
Doc retrival with time ::\n
    from datetime import datetime,timedelta
    t_0 = datetime.now()
    t_1 = t_0 + timedelta(0,30)
    t_2 = t_1 + timedelta(0,15)
    t_3 = t_0 + timedelta(0,55)

    # (if doc_uid=None, one is automatically generated)
    didSucceed,message = db.setDoc('users','keys',None,{'user_id':'sd89w3hr292r','key':'a0jd103b2r','timestamp':t_0})
    didSucceed,message = db.setDoc('users','keys',None,{'user_id':'sd89w3hr292r','key':'w8dh28232f','timestamp':t_1})
    didSucceed,message = db.setDoc('users','keys',None,{'user_id':'sd89w3hr292r','key':'89yf9hgfwe','timestamp':t_2})
    didSucceed,message = db.setDoc('users','keys',None,{'user_id':'sd89w3hr292r','key':'edhe2dqw9d','timestamp':t_3})
    
    ts = t_1 - timedelta(0,1)
    te = t_2 + timedelta(0,1)
    docs,didSucceed,message = db.getDocsByPattern('users','keys',{'timestamp':{ '$gte':ts,'$lte':te } })
    print docs
        >>> [{u'timestamp': '2015-01-23 10:57:14.779000', u'_id': '54c2996c319da682ebb17576', u'user_id': u'sd89w3hr292r', u'key': u'w8dh28232f'}, {u'timestamp': '2015-01-23 10:57:29.779000', u'_id': '54c2996c319da682ebb17577', u'user_id': u'sd89w3hr292r', u'key': u'89yf9hgfwe'}]

"""

from pymongo import MongoClient
import next.constants as constants
from bson.binary import Binary
import cPickle
import traceback
from datetime import datetime


class PermStore(object):
    """
    Acts as API to permanent store that can be passed around. Implements MongoDB

    Attribtues:
        client : MongoDB client
    """
    def __init__(self): 
        self.client = MongoClient(constants.MONGODB_HOST, constants.MONGODB_PORT)
#        self.client.write_concern = {'w':0}

    def __del__(self):
        try:
            if self.client!=None:
                self.client.close()
        except:
            pass

    def connectToMongoServer(self):
        try:
            self.client = MongoClient(constants.MONGODB_HOST, constants.MONGODB_PORT)

            
            if self.assertConnection():
                # This makes it so the write signal is fired off and and does not wait for acknowledgment
#                self.client.write_concern = {'w':0}
                return True,''
            else:
                raise
                error = 'Failed to connect to Mongodb server at %s:%s' % (constants.MONGODB_HOST,constants.MONGODB_PORT)
                return False,error
            return didSuccessfullyConnect,''
        except:
            return False,'Failed to connect to MongoDB Server'

    def assertConnection(self):
        """
        Checks that MongoDB is running

        Inputs:
            None

        Outputs:
            (boolean) isConnected

        Usage: ::\n
            db.assertConnection()
        """
        try:
            return bool(self.client.admin.command('ping')['ok'])
        except:
            return False




    def makeProperDatabaseFormat(self,input_val):
        """
        Example of usage: ::\n
            >>> from next.database.PermStore import PermStore
            >>> db = PermStore()
            >>> import numpy
            >>> X = numpy.zeros(3)
            >>> from datetime import datetime
            >>> timestamp = datetime.now()
            >>> input = {'animal':'dog','age':4.5,'x':X,'time':timestamp}
            >>> db_input = db.makeProperDatabaseFormat(input)
            >>> db_input
            {'x': Binary('\x80\x02cnumpy.core.multiarray\n_reconstruct\nq\x01cnumpy\nndarray\nq\x02K\x00\x85U\x01b\x87Rq\x03(K\x01K\x03\x85cnumpy\ndtype\nq\x04U\x02f8K\x00K\x01\x87Rq\x05(K\x03U\x01<NNNJ\xff\xff\xff\xffJ\xff\xff\xff\xffK\x00tb\x89U\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00tb.', 0), 'age': 4.5, 'animal': 'dog', 'time': datetime.datetime(2015, 1, 23, 10, 32, 28, 770190)}
            >>> db_output = db.undoDatabaseFormat(db_input)
            >>> db_output
            {'x': array([ 0.,  0.,  0.]), 'age': 4.5, 'animal': 'dog', 'time': datetime.datetime(2015, 1, 23, 10, 32, 28, 770190)}
            >>> input
            {'x': array([ 0.,  0.,  0.]), 'age': 4.5, 'animal': 'dog', 'time': datetime.datetime(2015, 1, 23, 10, 32, 28, 770190)}
        """

        if isinstance(input_val,dict):
            for key in input_val:
                input_val[key] = self.makeProperDatabaseFormat(input_val[key])
        elif isinstance(input_val,list):
            for idx in range(len(input_val)):
                input_val[idx] = self.makeProperDatabaseFormat(input_val[idx])
        elif isinstance(input_val, basestring):
            pass
        elif isinstance(input_val, (int, long, float) ):
            pass
        elif isinstance(input_val, datetime ):
            pass
        else:
            # pickle value so we can handle any python type
            pickled_input = cPickle.dumps(input_val, protocol=2)
            input_val = Binary(pickled_input)
        return input_val
    
    def undoDatabaseFormat(self,input_val):
        if isinstance(input_val,dict):
            for key in input_val:
                input_val[key] = self.undoDatabaseFormat(input_val[key])
        elif isinstance(input_val,list):
            for idx in range(len(input_val)):
                input_val[idx] = self.undoDatabaseFormat(input_val[idx])
        elif isinstance(input_val, Binary):
            input_val = cPickle.loads(input_val)
        return input_val
    
    
    def get_index_information(self,database_id,bucket_id):
        """
        Returns the description of all the indexes on the bucket
        """
        info = self.client[database_id][bucket_id].index_information()
        return info,True,''

    def create_index(self,database_id,bucket_id,index_dict):
        """
        Creates an index on the bucket defined by the keys in index_dict

        self.client[database_id][bucket_id].create_index( {'num_eyes':1} )
        """

        try:
            index_list = []
            for key in index_dict:
                index_list.append( (key,index_dict[key]) )
            message = self.client[database_id][bucket_id].create_index( index_list )
            return True,message
        except:
            return False,'unknown error'

    def drop_index(self,database_id,bucket_id,index_name):
        """
        Deletes the index named index_name defined over the bucket_id

        Inputs:
            (string) database_id, (string) index_name

        Outputs:
            (bool) didSucceed, (string) message 
        """
        message = self.client[database_id][bucket_id].create_index( index_list )
        return True,message

    def drop_all_indexes(self,database_id,bucket_id):
        """
        Deletes the index named index_name defined over the bucket_id

        Inputs:
            (string) database_id, (string) index_name

        Outputs:
            (bool) didSucceed, (string) message 
        """
        message = self.client[database_id][bucket_id].drop_indexes()
        return True,message
     


    def exists(self,database_id,bucket_id,doc_uid,key):
        """
        Check existence of key
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs: 
            (bool) exists, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            exists,didSucceed,message = db.exists(database_id,bucket_id,doc_uid,key)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            doc = self.client[database_id][bucket_id].find_one({"_id":doc_uid,key: { '$exists': True }})

            key_exists = (doc!=None)

            return key_exists,True,''
        except:
            error = "MongoDB.exists Failed with unknown exception"
            return None,False,error

    def get(self,database_id,bucket_id,doc_uid,key):
        """
        Get a value corresponding to key, returns None if no key exists
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key
        
        Outputs: 
            (string) value, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            value,didSucceed,message = db.get(database_id,bucket_id,doc_uid,key)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            doc = self.client[database_id][bucket_id].find_one({"_id":doc_uid,key: { '$exists': True }})
            if doc == None:
                message = 'MongoDB.get Key '+bucket_id+'.'+doc_uid+'.'+key+' does not exist'
                return None,True,message
            value = doc[key]

            return_value = self.undoDatabaseFormat(value)

            return return_value,True,'From MongoDB'

        except:
            return None,False,'MongoDB.get Failed with unknown exception'

    def getDoc(self,database_id,bucket_id,doc_uid):
        """
        get a doc (dictionary of string values) corresponding to a doc_uid with {"doc_uid":doc_uid} (if none, returns None)
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid
        
        Outputs: 
            ({ (string) key: (string) value, ... }) doc, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            doc,didSucceed,message = db.getDoc(database_id,bucket_id,doc_uid)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            doc = self.client[database_id][bucket_id].find_one({"_id":doc_uid})
            return_doc = self.undoDatabaseFormat(doc)

            return return_doc,True,''
        except:
            raise
            error = "MongoDB.getDoc Failed with unknown exception"
            return None,False,error

    def getDocsByPattern(self,database_id,bucket_id,filter_dict):
        """
        get all docs that contain {key1:value1,...} according to filter dict (if none, returns None)
        
        Inputs: 
            (string) database_id, (string) bucket_id, (dict of key ,value strings)
        
        Outputs: 
            ({ (string) key: (string) value, ... }) docs, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            docs,didSucceed,message = db.getDocsByPattern(database_id,bucket_id,filter_dict)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            docs_iterator = self.client[database_id][bucket_id].find( filter_dict  )
            
            docs = []
            for doc in docs_iterator:
                doc = self.undoDatabaseFormat(doc)
                
                try:
                    doc['_id'] = str(doc['_id'])
                except:
                    pass
                
                try:
                    doc['timestamp'] = str(doc['timestamp'])
                except:
                    pass
                
                docs.append(doc)

            return docs,True,''
        except:
            error = "MongoDB.getDocs Failed with unknown exception"
            return None,False,error


    def increment(self,database_id,bucket_id,doc_uid,key,value):
        """
        increments a key by amount value. If key does not exist, sets {key:value}
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, (string) key, (int) value
        
        Outputs:
            (int) new_value, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            new_value,didSucceed,message = db.increment(database_id,bucket_id,doc_uid,key,value)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            new_doc = self.client[database_id][bucket_id].find_and_modify(query={"_id":doc_uid} , update={ '$inc': {key:value} },upsert = True,new=True )
            new_value = new_doc[key]
            return new_value,True,'From Mongo'
        except:
            raise
            error = "MongoDB.set Failed with unknown exception"
            return False,error

    def increment_many(self,database_id,bucket_id,doc_uid,key_value_dict):
        """
        increments a key by amount value. If key does not exist, sets {key:value}
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, ({(str)key1:(float)value1,(int)key2:(float) value2}) key_value_dict
        
        Outputs:
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.increment_many(database_id,bucket_id,doc_uid,key_value_dict)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            self.client[database_id][bucket_id].update({"_id":doc_uid},{ '$inc': key_value_dict } )
            return True,'From Mongo'
        except:
            raise
            error = "MongoDB.set Failed with unknown exception"
            return False,error

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
        return self.get(database_id,bucket_id,doc_uid,key)

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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            value = self.makeProperDatabaseFormat(value)

            message = self.client[database_id][bucket_id].update( {"_id":doc_uid} , { '$push': {key:value} },upsert = True )

            return True,message
        except:
            raise
            error = "MongoDB.set Failed with unknown exception"
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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            
            value_list = self.makeProperDatabaseFormat(value_list)

            self.client[database_id][bucket_id].update( {"_id":doc_uid} , { '$unset': {key: '' } },upsert = True )
            self.client[database_id][bucket_id].update( {"_id":doc_uid} , { '$push': {key: { '$each': value_list } } },upsert = True )

            return True,''
        except:
            raise
            error = "MongoDB.set Failed with unknown exception"
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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            
            value = self.makeProperDatabaseFormat(value)

            message = self.client[database_id][bucket_id].update( {"_id":doc_uid} , { '$set': {key:value} },upsert = True )

            return True,''
        except:
            raise
            error = "MongoDB.set Failed with unknown exception"
            return False,error

    def setDoc(self,database_id,bucket_id,doc_uid,doc):
        """
        set a doc (dictionary of string values). If doc_uid==None, uid automatically assigned
        
        Inputs: 
            (string) database_id, (string) bucket_id, (string) doc_uid, ({ (string) key: (string) value, ... }) doc
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.setDoc(database_id,bucket_id,doc_uid,key,value)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            if doc_uid != None:
                doc['_id'] = doc_uid

            doc = self.makeProperDatabaseFormat(doc)
            write_id = self.client[database_id][bucket_id].insert(doc)
                
            return True,''
        except:
            error = "MongoDB.insert Failed with unknown exception"
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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            self.client[database_id][bucket_id].update( {"_id":doc_uid} , { '$unset': {key:1} })

            return True,"MongoDB.delete"
        except:
            error = "MongoDB.deleteBucket Failed with unknown exception"
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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            self.client[database_id][bucket_id].remove( {'_id':doc_uid} )

            return True,''
        except:
            error = "MongoDB.deleteBucket Failed with unknown exception"
            return False,error

    def deleteDocsByPattern(self,database_id,bucket_id,filter_dict):
        """
        delete all docs that contain {key1:value1,...} according to filter dict (if none, returns None)
        
        Inputs: 
            (string) database_id, (string) bucket_id, (dict of key,value strings)
        
        Outputs: 
            ({ (string) key: (string) value, ... }) docs, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.deleteDocsByPattern(database_id,bucket_id,filter_dict)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return False,message

        try:
            dict_return = self.client[database_id][bucket_id].remove( filter_dict  )
            return True,str(dict_return)
        except Exception, err:
            error = traceback.format_exc()
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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            self.client[database_id][bucket_id].drop()

            return True,''
        except:
            error = "MongoDB.deleteBucket Failed with unknown exception"
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
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            self.client.drop_database(database_id)

            return True,''
        except:
            error = "MongoDB.deleteDatabase Failed with unknown exception"
            return False,error

    def deleteAll(self):
        """
        delete all databases (i.e. everything)
        
        Inputs: 
            None
        
        Outputs: 
            (bool) didSucceed, (string) message 
        
        Usage: ::\n
            didSucceed,message = db.deleteAll()
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            db_list = self.client.database_names()
            for database_id in db_list:
                if (database_id != 'local') and (database_id != 'admin'):
                    didSucceed,message = self.deleteDatabase(database_id)

            return True,''
        except:
            error = "MongoDB.deleteDatabase Failed with unknown exception"
            return False,error



    def getDocNames(self,database_id,bucket_id):
        """
        get list of doc_uids correspding to all the docs in the bucket corresponding to the given bucket_id
            
        Inputs: 
            (string) database_id, (string) bucket_id
        
        Outputs: 
            ([(string) doc_uid, ... ]) docNames, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            docNames,didSucceed,message = db.getDocNames(database_id,bucket_id)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            docs_iterator = self.client[database_id][bucket_id].find()
            doc_names = [doc['_id'] for doc in docs_iterator]

            return doc_names,True,''
        except:
            error = "MongoDB.getDocNames Failed with unknown exception"
            return None,False,error

    def getBucketNames(self,database_id):
        """
        get list of bucket_ids for corresponding database_id
        
        Inputs: 
            (string) database_id
        
        Outputs: 
            ([(string) bucket_id, ... ]) docNames, (bool) didSucceed, (string) message 
        
        Usage: ::\n
            bucketNames,didSucceed,message = db.getBucketNames(database_id)
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            buckets_iterator = self.client[database_id].collection_names()
            bucket_names = [bucket for bucket in buckets_iterator]

            return bucket_names,True,''
        except:
            error = "MongoDB.getBucketNames Failed with unknown exception"
            return None,False,error

    def getDatabaseNames(self):
        """
        gets list of database names (currently just app_data and app_logs, by default all above methods only funciton on app_data aside from the logs)
        
        Inputs: 
            None
        
        Outputs: 
            ([(string) bucket_id, ... ]) databaseNames, (bool) didSucceed, (string) message 
        
        Usage:
            databaseNames,didSucceed,message = db.getDatabaseNames()
        """
        if self.client == None:
            didSucceed,message = self.connectToMongoServer()
            if not didSucceed:
                return None,False,message

        try:
            databases_iterator = self.client.database_names()
            database_names = [database for database in databases_iterator]

            return database_names,True,''
        except:
            error = "MongoDB.getDatabaseNames Failed with unknown exception"
            return None,False,error

    


