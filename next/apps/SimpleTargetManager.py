class SimpleTargetManager(object):
    def __init__(self):
        self.database_id = 'app_data'
        self.bucket_id = 'targets'

    def set_targetset(self, exp_uid, targetset, db):
        """
        Update the default target docs in the DB if a user uploads a target set.
        """
        for i in range(len(targetset)):
            target = targetset[i]
            target['target_id'] = i
            target['exp_uid'] = exp_uid
            didSucceed, message = db.setDoc(self.database_id, self.bucket_id, None, target)
            if not didSucceed:
                raise Exception("Failed to create_target_mapping: {}".format(message))

    def get_targetset(self, exp_uid, db):
        """
        Gets the entire targetset for a given experiment as a list of dictionaries.
        """
        mongotized_target_blob, didSucceed, message = db.getDocsByPattern(self.database_id,
                                                                          self.bucket_id,
                                                                          {'exp_uid': exp_uid})
        if not didSucceed:
            raise Exception("Failed to create_target_mapping: {}".format(message))
        targetset = mongotized_target_blob.pop(0)
        return targetset

    def get_target_item(self, exp_uid, target_id, db):
        """
        Get a target from the targetset. Th
        """
        # Get an individual target form the DB given exp_uid and index
        got_target, didSucceed, message = db.getDocsByPattern(self.database_id,
                                                              self.bucket_id,
                                                              {'exp_uid': exp_uid,
                                                               'target_id': target_id})
        try:
            target = got_target.pop(0)
        except:
            target = {'target_id':target_id,
                      'primary_description':str(target_id),
                      'primary_type':'text',
                      'alt_description':str(target_id),
                      'alt_type':'text'}
        if not didSucceed:
            raise Exception("Failed to get_target_item given index: {}".format(message))
        del target['exp_uid']
        return target

