import json
import next.utils as utils
import next.apps.SimpleTargetManager

class PoolBasedTripletMDS(object):
    def __init__(self,db):
        self.app_id = 'PoolBasedTripletMDS'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, exp_data):
        exp_uid = butler.exp_uid
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_uid, exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']

        alg_data = {}
        algorithm_keys = ['n','d','failure_probability']
        for key in algorithm_keys:
            if key in exp_data['args']:
                alg_data[key]=exp_data['args'][key]

        return exp_data,alg_data

    def getQuery(self, butler, query_request, alg_response):
        exp_uid = butler.exp_uid
        center  = self.TargetManager.get_target_item(exp_uid, alg_response[0])
        left  = self.TargetManager.get_target_item(exp_uid, alg_response[1])
        right  = self.TargetManager.get_target_item(exp_uid, alg_response[2])
        center['label'] = 'center'
        left['label'] = 'left'
        right['label'] = 'right'
        return {'target_indices':[center, left, right]}

    def processAnswer(self, butler, query, answer):
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'center':
                center_id = target['target_id']
            elif target['label'] == 'left':
                left_id = target['target_id']
            elif target['label'] == 'right':
                right_id = target['target_id']
        target_winner = answer['args']['target_winner']
        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])
        
        n = experiment['args']['n']
        if num_reported_answers % ((n+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':butler.exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        q = [left_id, right_id,center_id] if target_winner==left_id else [right_id, left_id,center_id]

        algs_args_dict = {'left_id':left_id, 'right_id':right_id, 'center_id':center_id, 'target_winner':target_winner}
        query_update = {'target_winner':target_winner, 'q':q}
        return query_update,algs_args_dict

    def getModel(self, butler, args_dict, alg_response):
        return {'Xd':alg_response[0], 'num_reported_answers':alg_response[1]}



