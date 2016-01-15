
class Targetsets(object):
    def __init__(self):
        self.database_id = 'app_data'
        self.bucket_id = 'targets'

    def set_targetset(self, exp_uid, targetset):
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
            (string) exp_uid, (list of dictionaries) targetset
        Outputs:
            (boolean) didSucceed

        Usage: ::\n
        didSucceed = targetmapper.create_target_mapping(exp_uid, target_blob)
        {'target_id': superhappy, 'index': 23, 'primary_description': s3.com/superhappy, 'primary_type': img, 'alt_description': a super happy person, 'features': features}
        """

        # Iteratively initilize target documents and insert into MongoDB
        for i in range(len(targetset)):
            # Get the target from the list
            target = targetset[i]

            # Structure target document for MongoDB
            doc = {'index': i,
                   'target_id': target['target_id'],
                   'primary_description': target['primary_description'],
                   'primary_type': target['primary_type'],
                   'alt_description': target['alt_description'],
                   'alt_type': target['alt_type'],
                   'exp_uid': exp_uid}

            didSucceed, message = db.setDoc(self.database_id, self.bucket_id, None, doc)

            # If target not successfully created, throw an error
            if not didSucceed:
                raise DatabaseException("Failed to create_target_mapping: {}".format(message))

    def get_targetset(self, exp_uid):
        """
        Gets the entire targetset for a given experiment as a list of dictionaries.
        """
        # Get all docs related to the specified exp_uid
        mongotized_target_blob, didSucceed, message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid})

        # If the newly initialized DB docs can't be found, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to create_target_mapping: {}".format(message))

        # Pop target_dict out of list
        targetset = mongotized_target_blob.pop(0)

        # Return a list of all targets corresponding to current exp_uid
        return targetset

    def get_target_item(self, exp_uid, index):
        """
        Get a target from the targetset. Th

        :param exp_uid: (string) The unique identifier of the expeiment.
        :param index: (int) The index corresponding to the target in the targetset. If
                      the desired target was the third item in the list, index==3.
        :returns: The specified target as a dictionary, targetset[index].
        """
        # Get an individual target form the DB given exp_uid and index
        got_target, didSucceed, message = db.getDocsByPattern(self.database_id, self.bucket_id, {'exp_uid': exp_uid, 'index': index})

        # I'm not sure if getDocsByPattern will return list if only 1 doc is
        # retrevied. If this fails, remove this line.
        try:
            target = got_target.pop(0)
        except:
            pass

        # If doc cannot be retreived, throw an error
        if not didSucceed:
            raise DatabaseException("Failed to get_target_item given index: {}".format(message))

        return target

