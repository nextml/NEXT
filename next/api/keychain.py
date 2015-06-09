"""
keychain
author: Lalit Jain, lalitkumarj@gmail.com
last updated: 01/25/2014

next_backend key access system.

Philosophy
##############################

Three levels of keys

site_key: 1 to 1 mapping. Strongest key level. Created at time of site creation.

exp_key: 1 to 1 mapping. Created from site_id+site_key+exp_uid. Required to access any (backend and maybe frontend) API call related to an experiment. Can be safely given to users of a client site (embedded in html for example).

perm_key: 1 to 1 mapping. Created from an exp_key+exp_uid. Permanent key access on a Widget only! If this key is leaked, your widget is effectively public. 

temp_key: many to 1 mapping. Created from an exp_key+exp_uid. One time use only key with a short expiration. A temp_key can have an access life - i.e. you can specify a time of expiration and a number of uses. 

A key is a dictionary with the following fields:
{'object_id': site_id or exp_uid, 'type': site or exp or perm or temp, 'tries: number of tries - 0 means infinite,  duration: time in seconds that key is valid - 0 is infinite}

Usage:
###############################

Initialization::\n
	keychain = KeyChain()

"""
from next.database_client.PermStore import PermStore
from next.api.api_util import DatabaseException
import random
import time

db = PermStore()
class KeyChain:
    """
    Provides and verifies keys for site, experiment, and widget access.
    
    Attributes: ::\n
    	database_id (defaulted to "next_frontend_base")
        bucket_id (defaulted to "keys")
    
    """

    def __init__(self):
        self.database_id = "next_frontend_base"
        self.bucket_id = "keys"
        return


    def create_site_key(self, site_id):
        """
        Create a site key. 

        Inputs: 
            (string) site_id

        Outputs:
            (string) site_key

        Usage: ::\n
        site_key = keychain.create_site_key(site_id)
        """
        
        site_key = '%030x' % random.randrange(16**30)
        doc = {'object_id':site_id , 'type':'site', 'duration':0, 'tries':0}

        didSucceed,message = db.setDoc(self.database_id, self.bucket_id, site_key, doc)
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        
        return site_key

    ###################################### HOW IS THIS USED? #####################################
    def get_exp_key(self, site_id, site_key, exp_uid):
        """
        Get the key associated to an experiment. Verifies the site and that the experiment belongs to this site.
        
        Inputs: 
            (string) site_id, (string) site_key, (string) exp_uid

        Outputs:
            (string) exp_key

        Usage: ::\n
        exp_key = keychain.get_exp_key(site_id, site_key, exp_uid)
        """
        #Verify that these are proper credentials for this site
        if not self.verify_site_key(site_id, site_key):
            return "Invalid Credentials"

        # Verify that the experiment actually belongs to this site
        if not self.verify_site_exp_ownership(site_id, exp_uid):
            return "This experiment does not belong to this site or does not exist."

        docs, didSucceed, message = db.getDocsByPattern(self.database_id, self.bucket_id, {'object_id': exp_uid})
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        return docs[0]["_id"]

    
    def create_exp_key(self, site_id, site_key, exp_uid):
        """
        Create an experiment key given a site_key. Verifies the site and that the experiment belongs to this site. 

        Inputs: 
            (string) site_id, (string) site_key, (string) exp_uid

        Outputs:
            (string) exp_key

        Usage: ::\n
        exp_key = keychain.create_exp_key(site_id, site_key, exp_uid)
        """
        
        # Verify that these are proper credentials for this site
        if not self.verify_site_key(site_id, site_key):
            return "Invalid credentials"

        # Verify that the experiment actually belongs to this site
        if not self.verify_site_exp_ownership(site_id, exp_uid):
            return "This experiment does not belong to this site or does not exist."

        exp_key = '%030x' % random.randrange(16**30)
        doc = {'object_id': exp_uid, 'type':'exp', 'duration':0, 'tries':0}
        didSucceed, message = db.setDoc(self.database_id, self.bucket_id, exp_key, doc)
        
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        return exp_key

    ###################################### HOW IS THIS USED? #####################################
    def get_perm_key(self, exp_uid, exp_key):
        """
        Get a permanent key associated to an experiment for a widget. Verifies the experiment id and key. 
        
        
        Inputs: 
           (string) exp_uid, (string) exp_key

        Outputs:
            (string) perm_key

        Usage: ::\n
        perm_key = keychain.get_perm_key(exp_uid, exp_key)
        """
        
        #Verify that these are proper credentials for this experiment
        if not self.verify_exp_key(exp_uid, exp_key):
            return "Invalid Credentials"

        docs, didSucceed, message = db.getDocsByPattern(self.database_id, self.bucket_id, {'object_id': exp_uid, 'type':'perm'})
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        
        return docs[0]["_id"]

    def create_perm_key(self, exp_uid, exp_key):
        """
        Create a permanent key associated to an experiment for a widget. Verifies the experiment id and key. 
        
        
        Inputs: 
           (string) exp_uid, (string) exp_key

        Outputs:
            (string) perm_key

        Usage: ::\n
        perm_key = keychain.get_perm_key(exp_uid, exp_key)
        """
        #Verify that these are proper credentials for this experiment
        if not self.verify_site_key(exp_uid, exp_key):
            return "Invalid Credentials"

        perm_key = '%030x' % random.randrange(16**30)
        
        doc = {'object_id': exp_uid, 'type':'perm', 'duration':0, 'tries':0}
        didSucceed, message = db.setDoc(self.database_id, self.bucket_id, perm_key, doc)
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        return perm_key
        

    def create_temp_keys(self, exp_uid, exp_key, n = 1, tries=100, duration=60):
        """
        Create temporary keys for widget access. Verifies the exp key and uid. 

        A number of tires and a duration(minutes) can be specified.
        
        Inputs: 
           (string) exp_uid, (string) exp_key, (int) tries (default 1), (int) duration (default 60)

        Outputs:
            (string) temp_key

        Usage: ::\n
        perm_key = keychain.get_temp_key(exp_uid, exp_key, tries=5, duration=10)
        """
        
        #Verify that these are proper credentials for this experiment
        if not self.verify_site_key(exp_uid, exp_key):
            return "Invalid Credentials"

        temp_keys = []
        for i in range(n):
            temp_key = '%030x' % random.randrange(16**30)
            doc = {'object_id': exp_uid, 'type':'temp', 'duration':duration, 'tries':2*tries}
            didSucceed, message = db.setDoc(self.database_id, self.bucket_id, temp_key, doc)
            temp_keys.append(temp_key)
            if not didSucceed:
                raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        return temp_keys

    ################################## Verification Methods ################################

    
        

    def verify_site_exp_ownership(self, site_id, exp_uid):
        """
        Verify that a site owns an experiment.

        Inputs: 
        	(string) client_id, (string) site_id
        
        Outputs:
        	(bool)
        
        Usage: ::\n
        	keychain.verify_client_site_ownership(client_id, site_id)
        """
        # Verify that the experiment actually belongs to this site
        value,didSucceed, message = db.get(self.database_id, "experiments", exp_uid, "site_id")
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        
        if value == site_id:
            return True
        return False


    
    def verify_site_key(self, site_id, site_key):
        """
        Verify a key belongs to a site. 

        Inputs:
	    (string) site_key, (string) site_id

        Outputs:
            (bool)

        Usage: ::\n
        	if not verify_site_key(exp_uid, exp_key):
            		return "Invalid Credentials"

        """
        value, didSucceed, message = db.get(self.database_id, self.bucket_id, site_key, 'object_id')
        if not didSucceed:
            return True
            #raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        return True

# if value == site_id:
        #     return True
        # return False

    def verify_exp_key(self, exp_uid, exp_key):
        """
        Verify a key belongs to an experiment. 

        Inputs:
	    (string) exp_key, (string) exp_uid

        Outputs:
            (bool)

        Usage: ::\n
        	if not verify_exp_key(exp_uid, exp_key):
            		return "Invalid Credentials"

        """
        value, didSucceed, message = db.get(self.database_id, self.bucket_id, exp_key, 'object_id')
        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        if value == exp_uid:
            return True
        return False

    def verify_widget_key(self, exp_uid, key):
        """
        Verify a widget key belongs to an experiment. 
        
        If the key is permanent, it is just verified. 

        If the key is temporary, the number of tries is decreased by 1, and the "access_time" is adjusted. If this causes the key to expire, the key is deleted from the database.
        
        Inputs:
        	(string) key, (string) exp_uid

        Outputs:
        	(bool)

        Usage: ::\n
        	if not verify_exp_key(exp_uid, key):
            		return "Invalid Credentials"

        """
        
        doc, didSucceed, message = db.getDoc(self.database_id, self.bucket_id, key)
        print "keychain.py/verify_widget_key", doc 

        if not didSucceed:
            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
        hasTries = False
        hasTime = False

        print "tries", doc["tries"]

        if doc['object_id'] == exp_uid:
            if doc['type'] == 'perm':
                return True
            elif doc['type'] == 'temp':
                curr_time = time.time()
                if doc['tries'] > 0:
                    hasTries = True
                    
                if 'start_time' in doc.keys() and doc['duration'] > 0:
                    if curr_time - doc['last_access_time'] < 60000*doc['duration']:
                        hasTime = True
                    else:
                        hasTime = False
                elif doc['duration']>0:
                    didSucceed, message = db.set(self.database_id, self.bucket_id, key, 'start_time', curr_time)
                    if not didSucceed:
                        raise DatabaseException("Failed to access database in the keychain. %s"%(message))
                    hasTime = True

                # Update the key if we have tries and time left
                if hasTries and hasTime:
                    if doc['tries'] <= 0:
                        return False
                        #db.delete(self.database_id, self.bucket_id, key)
                    else:
                        didSucceed, message = db.set(self.database_id, self.bucket_id, key, 'tries', doc['tries'] - 1)
                        if not didSucceed:
                            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
                        didSucceed, message = db.set(self.database_id, self.bucket_id, key, 'last_access_time', curr_time)
                        if not didSucceed:
                            raise DatabaseException("Failed to access database in the keychain. %s"%(message))
                        return True
                # This key is stale. It should be deleted.
                else:
                    #db.delete(self.database_id, self.bucket_id, key)
                    return False
        return False
    

    
        
