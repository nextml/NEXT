import json
import next.utils as utils
import next.apps.SimpleTargetManager

class PoolBasedBinaryClassification(object):
    def __init__(self,db):
        self.app_id = 'PoolBasedBinaryClassification'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, exp_data):
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(butler.exp_uid, exp_data['args']['targets']['targetset'])

        d = len(exp_data['args']['targets']['targetset'][0]['meta']['features'])
        exp_data['args']['n'] = n
        exp_data['args']['d'] = d
        del exp_data['args']['targets']

        alg_data = {}
        algorithm_keys = ['n','failure_probability']
        for key in algorithm_keys:
            if key in exp_data['args']:
                alg_data[key]=exp_data['args'][key]

        return exp_data, alg_data

    def getQuery(self, butler, alg, args):
        args.pop('widget',None)
        alg_response = alg(args)
        utils.debug_print(alg_response)
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
        return alg({})



