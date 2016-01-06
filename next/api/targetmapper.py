"""
TargetMapper
author: Chris Fernandez, crfernandez@wisc.edu

last updated: 02/27/2015

The next_frontend_base target association system.

The need-to-knows:
1. Upon initialization, experiments DEFAULT (targetless) state is defined by the init_empty_target_mapping function.
2. If a target set is provided, the default target DB objects are CREATED with real target data and targetless is set to False.
3. get_target_data is used to retrieve target DB objects. exp_uid and target index must be specified. If target_index is not known, use get_index_given_targetID.
4. Two types of ERRORS can occur can occur in target_mapper:
    a. "Invalid TargetMap Format. Please check your target upload CSV file and include all of the required feilds."
        This error occurs when a user uploads a target dataset that does not contain all of the required feilds (below).
        This behavior should be handled in TargetEditor, and the specific missing feilds determined by the csv parser.
    b.  Errors from PermStore.py. All DB connections are checked in PermStore prior to trying to retrieve the data.
        Other than no connection to DB, errors can occur if the requested target_doc is not found, or if no such exp_uid exists.
        These PermStore error messages will be returned if they occur. This is agnostic to the module accessing TargetMapper.
        In practice, these errors would occur during get_target_data, and the specific error messages relayed the user are defined in getQuery API resource.

Individual targets submitted in create_target_mapping MUST contain the following REQUIRED metadata: 
    1. target_id: a unique target identifier init by the client
    2. index: the next_backend target object index
    3. primary_description: possibly image URI, or text
    4. primary_type: img/text/audio/etc, tells how to display primary_description in widget
    5. alternative_description: text descriptor, perhaps a caption for the image or subtitle for primary_description
    6. features: list of floats, this will also be saved in the backend

Target DB objects are RETURNED in the following dictionary format:
    {'exp_uid': exp_uid 'target_id': superhappy, 'n': 23, 'primary_description': s3.com/superhappy, ..
    'primary_type': img, 'alt_description': 'a super happy person', 'features': features}

Initialization::\n
	targetmapper = targetmapper()

"""
from next.database_client.PermStore import PermStore
from next.api.api_util import DatabaseException

db = PermStore()
class TargetMapper:
    """
    Provides and mapps targets and metadata for site, experiment, and widget access.
    
    Attributes: ::\n
    	database_id (defaulted to "next_frontend_base")
        bucket_id (defaulted to "targets")
    """
    def __init__(self):
        self.database_id = "next_frontend_base"
        self.bucket_id = "targets"
        return

    def init_empty_target_mapping(self, exp_uid, n):
        """
        Create a target doc that indicates a targetless experiment, the default state upon initialization.
        This doc is formatted as follows:
        {'targetless': True, 'exp_uid': exp_uid}

        Inputs: 
            (string) exp_uid, (int) n
        Outputs:
            (dict) {}

        Usage: ::\n
        didSucceed = targetmapper.init_empty_target_mapping(exp_uid)
        """
        didSucceed, message = db.create_index(self.database_id, self.bucket_id, {'exp_uid':1})
        didSucceed, message = db.create_index(self.database_id, self.bucket_id, {'exp_uid':1,'index':1})
        didSucceed, message = db.create_index(self.database_id, self.bucket_id, {'exp_uid':1,'target_id':1})
        didSucceed, message = db.create_index(self.database_id, self.bucket_id, {'exp_uid':1,'targetless':1})

        # Initilize target document and insert into MongoDB
        doc = {'targetless': True, 'exp_uid': exp_uid}
        didSucceed, message = db.setDoc(self.database_id, self.bucket_id, None, doc)
        # If target doc could not be created, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to init_empty_target_mapping: %s"%(message))           
        # Get all docs related to the specified exp_uid
        mongotized_target_blob,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid})
        # If the newly initialized DB docs can't be found, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to init_empty_target_mapping: %s"%(message))
        # Pop target_dict out of list
        target_blob_dict = mongotized_target_blob.pop(0)
        # Return target_blob_dict of all targets corresponding to current exp_uid
        return {}       

    def create_target_mapping(self, exp_uid, target_blob):
        """
        Update the default target docs in the DB if a user uploads a target set.
        Target_blob should be a list of targets, with each individual target having the following format. All feilds are REQUIRED.
            target_id: a unique target identifier init by the client
            index: the next_backend target object index
            primary_description (possibly image URI, or text)
            primary_type (img/text/audio/etc, tells how to display primary_description in widget)
            alternative_description (text descriptor, perhaps a caption for the image or subtitle for primary_description)
            features (list of floats, this will also be saved in the backend but its best to save this here as well I think. disk space is effectively infinite)

        Inputs: 
            (string) exp_uid, (list) target_blob
        Outputs:
            (boolean) didSucceed

        Usage: ::\n
        didSucceed = targetmapper.create_target_mapping(exp_uid, target_blob)
        {'target_id': superhappy, 'index': 23, 'primary_description': s3.com/superhappy, 'primary_type': img, 'alt_description': a super happy person, 'features': features}
        """
        #Verify that target_blob object has valid target mapping format
        #if not self.verify_target_map_format(exp_uid, target_blob):
        #    print "Invalid TargetMap Format. Please check your target upload CSV file and include all of the required feilds."
        #    return "Invalid TargetMap Format. Please check your target upload CSV file and include all of the required feilds."

        # Delete target doc indicating targetless initialization
        didSucceed,message = db.deleteDocsByPattern(self.database_id,self.bucket_id,{'exp_uid': exp_uid, 'targetless': True})
        if not didSucceed:
            raise DatabaseException("Failed to create_target_mapping: %s"%(message))
        # Recreate target document to denote target mapping has been created
        doc = {'targetless': False, 'exp_uid': exp_uid}
        didSucceed, message = db.setDoc(self.database_id, self.bucket_id, None, doc)
        if not didSucceed:
            raise DatabaseException("Failed to create_target_mapping: %s"%(message))

        # Iteratively initilize target documents and insert into MongoDB
        for ii in range(len(target_blob)):
            # Parse target specific args out of target_blob at index ii
            target_tmp = target_blob[ii]
            target_id = target_tmp['target_id']
            index = ii
            primary_description = target_tmp['primary_description']            
            primary_type = target_tmp['primary_type']
            alt_type = target_tmp['alt_type']
            alt_description = target_tmp['alt_description']
            # Structure target document for MongoDB
            doc = {'index': index,
                   'target_id': target_id,
                   'primary_description': primary_description,
                   'primary_type': primary_type,
                   'alt_description': alt_description,
                   'alt_type': alt_type,
                   'exp_uid': exp_uid}
            didSucceed, message = db.setDoc(self.database_id, self.bucket_id, None, doc)

            # If target not successfully created, throw an error
            if not didSucceed:
                raise DatabaseException("Failed to create_target_mapping: %s"%(message))
             
        # Get all docs related to the specified exp_uid
        mongotized_target_blob,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid})
        
        # If the newly initialized DB docs can't be found, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to create_target_mapping: %s"%(message))
        # Pop target_dict out of list
        target_blob_dict = mongotized_target_blob.pop(0)

        # Return target_blob_dict of all targets corresponding to current exp_uid
        return target_blob_dict  

    def get_target_mapping(self, exp_uid):
        """
        Get the full target mapping. This be useful for pages that want to show/load the entire target set.

        Inputs: 
            (string) exp_uid
        Outputs:
            (boolean) target_data

        Usage: ::\n
        didSucceed = targetmapper.init_empty_target_mapping(exp_uid, n)
        """
        # Get all docs for specified exp_uid
        mongotized_target_blob,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid})
        # If no docs with exp_uid can be retreived, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to get_target_mapping: %s"%(message))
        # Pop target_blob_dict out of list
        for i in range(len(mongotized_target_blob)):
            if 'targetless' in mongotized_target_blob[i].keys():
                mongotized_target_blob.pop(i)
                break
        try:
            mongotized_target_blob = sorted(mongotized_target_blob,key = lambda x: x.get('index',0))
        except:
            pass
            
        target_blob_dict = mongotized_target_blob
        return target_blob_dict

    def get_target_data(self, exp_uid, index):
        """
        Get an individual targets metadata given that targets index.

        Inputs: 
            (string) exp_uid, index
        Outputs:
            (dict) target_data

        Usage: ::\n
        didSucceed = targetmapper.init_empty_target_mapping(exp_uid, n)
        """
        target_data,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'targetless': False})
        # Pass back message if getDocsByPattern fails
        if not didSucceed:
            raise DatabaseException("Failed to get_target_data: %s"%(message))
        # This line is key. If no doc exists with the specified exp_uid and targetless = True, then targetless = False
        if not target_data:
            return {'target_id':index,
                    'primary_description':index,
                    'primary_type':'text',
                    'alt_description':index,
                    'alt_type':'text'}
        # Get an individual target form the DB given exp_uid and index
        target_data,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'index':index})
        # If doc cannot be retreived, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to get_target_data: %s"%(message))
        # Pop target_dict out of list and return
        target_data_dict = target_data.pop(0)
        return target_data_dict

    def get_index_given_targetID(self, exp_uid, target_id):
        """
        Get the internal NEXT target index given a clients supplied target_id

        Inputs:
            (string) exp_uid, (string) target_id

        Outputs:
            (int) index

        Usage: ::\n
        didSucceed = targetmapper.get_index_given_targetID(exp_uid, target_id)
        """
        
        target_data,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'targetless': False})
        # Pass back message if getDocsByPattern fails
        if not didSucceed:
            raise DatabaseException("Failed to get_index_given_targetID: %s"%(message))
        # This line is key. If no doc exists with the specified exp_uid and targetless = True, then targetless = False
        if not target_data:
            return target_id
        # Get an individual target form the DB given exp_uid and target_id
        got_target,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'target_id': target_id})
        # If doc cannot be retreived, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to get_index_given_targetID: %s"%(message))
        # I'm not sure if getDocsByPattern will return list if only 1 doc is retrevied. If this fails, remove this line.
        got_target = got_target.pop(0)
        # Get index out of target dictionary
        index = got_target['index']
        return int(index)

    def get_targetID_given_index(self, exp_uid, index):
        """
        Get the client supplied target_id given an internal NEXT target index

        Inputs:
            (string) exp_uid, (int) index
        Outputs:
            (string) target_id

        Usage: ::\n
        didSucceed = targetmapper.get_targetID_given_index(exp_uid, index)
        """
        target_data,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'targetless': True})
        # Pass back message if getDocsByPattern fails
        if not didSucceed:
            raise DatabaseException("Failed to get_targetID_given_index: %s"%(message))
        # This line is key. If no doc exists with the specified exp_uid and targetless = True, then targetless = False
        if not target_data:
            return index

        # Get an individual target form the DB given exp_uid and index
        got_target,didSucceed,message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'index': index})
        # If doc cannot be retreived, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to get_targetID_given_index: %s"%(message))

        # I'm not sure if getDocsByPattern will return list if only 1 doc is retrevied. If this fails, remove this line.
        got_target = got_target.pop(0)
        # Get target_id out of target dictionary        
        target_id = got_target['target_id']
        return target_id

    def set_target_data(self):
        return 'This feature is not yet available!'

    def delete_target_data(self):
        return 'This feature is not yet available!'

    def verify_target_map_format(self, exp_uid, target_blob):
        # Enumeate target_blob (list of all submitted targets). Check for each required feild for each target and return false if not available.
        for target in enumerate(target_blob):
            if not target['target_id']: return False
            if not target['index']: return False
            if not target['primary_description']: return False
            if not target['primary_type']: return False
            if not target['alt_description']: return False
            if not target['features']: return False
        return True
