import json
import next.utils as utils
import next.apps.SimpleTargetManager

class PoolBasedTripletMDS(object):
    def __init__(self,db):
        self.app_id = 'PoolBasedTripletMDS'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):
        exp_uid = butler.exp_uid
        if 'targetset' in args['targets'].keys():
            n  = len(args['targets']['targetset'])
            self.TargetManager.set_targetset(exp_uid, args['targets']['targetset'])
        else:
            n = args['targets']['n']
        args['n'] = n
        del args['targets']

        alg_data = {}
        algorithm_keys = ['n','d','failure_probability']
        for key in algorithm_keys:
            if key in args:
                alg_data[key]=args[key]

        init_algs(alg_data)
        return args

    def getQuery(self, butler, alg, args):
        alg_response = alg()
        exp_uid = butler.exp_uid
        center  = self.TargetManager.get_target_item(exp_uid, alg_response[0])
        left  = self.TargetManager.get_target_item(exp_uid, alg_response[1])
        right  = self.TargetManager.get_target_item(exp_uid, alg_response[2])
        center['label'] = 'center'
        left['label'] = 'left'
        right['label'] = 'right'
        return {'target_indices':[center, left, right]}

    def processAnswer(self, butler, alg, args):
        query = butler.queries.get(uid=args['query_uid'])
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'center':
                center_id = target['target_id']
            elif target['label'] == 'left':
                left_id = target['target_id']
            elif target['label'] == 'right':
                right_id = target['target_id']
        target_winner = args['target_winner']
        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])
        
        n = experiment['args']['n']
        if num_reported_answers % ((n+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':butler.exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        q = [left_id, right_id,center_id] if target_winner==left_id else [right_id, left_id,center_id]

        alg({'left_id':left_id, 'right_id':right_id, 'center_id':center_id, 'target_winner':target_winner})
        return {'target_winner':target_winner, 'q':q}

    def getModel(self, butler, alg, args):
        return alg()




