import json
import next.utils as utils
import next.apps.SimpleTargetManager

class PoolBasedBinaryClassification(object):
    def __init__(self,db):
        self.app_id = 'PoolBasedBinaryClassification'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):
        args['n']  = len(args['targets']['targetset'])        
        # Get the first target, extract it's feature vector and save this as the dimension
        # This assumes that feature dimension consistent across all targets
        args['d'] = len(args['targets']['targetset'][0]['meta']['features'])
        targets = sorted(args['targets']['targetset'],key=lambda x: x['target_id'])
        self.TargetManager.set_targetset(butler.exp_uid, targets)
        del args['targets']
        
        alg_data = {'n': args['n'],
                    'failure_probability': args['failure_probability'],
                    'd': args['d']}
        init_algs(alg_data)
        return args

    def getQuery(self, butler, alg, args):
        alg_response = alg({'participant_uid':args['participant_uid']})
        target = self.TargetManager.get_target_item(butler.exp_uid, alg_response)
        del target['meta']
        return {'target_indices':target}

    def processAnswer(self, butler, alg, args):
        query = butler.queries.get(uid=args['query_uid'])
        target = query['target_indices']
        target_label = args['target_label']

        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        d = experiment['args']['d']
        if num_reported_answers % ((d+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':butler.exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))

        alg({'target_index':target['target_id'],'target_label':target_label})
        return {'target_index':target['target_id'],'target_label':target_label}

    def getModel(self, butler, alg, args):
        return alg()

