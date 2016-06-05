import json
import next.utils as utils
import next.apps.SimpleTargetManager

class PoolBasedBinaryClassification(object):
    def __init__(self,db):
        self.app_id = 'PoolBasedBinaryClassification'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, exp_uid, exp_data, butler):
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_uid, exp_data['args']['targets']['targetset'])
        d = len(exp_data['args']['targets']['targetset'][0]['meta']['features'])
        exp_data['args']['n'] = n
        exp_data['args']['d'] = d
        del exp_data['args']['targets']

        alg_data = {}
        algorithm_keys = ['n','failure_probability']
        for key in algorithm_keys:
            if key in exp_data['args']:
                alg_data[key]=exp_data['args'][key]

        return exp_data,alg_data

    def getQuery(self, exp_uid, experiment_dict, query_request, alg_response, butler):
        target  = self.TargetManager.get_target_item(exp_uid, alg_response)
        del target['meta']
        return {'target_indices':target}

    def processAnswer(self, exp_uid, query, answer, butler):
        target = query['target_indices']
        target_label = answer['args']['target_label']

        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])
        
        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        d = experiment['args']['d']
        if num_reported_answers % ((d+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        

        algs_args_dict = {'target_index':target['target_id'],'target_label':target_label}
        query_update = {'target_index':target['target_id'],'target_label':target_label}
        return query_update,algs_args_dict

    def getModel(self, exp_uid, alg_response, args_dict, butler):
        return {'weights':alg_response[0], 'num_reported_answers':alg_response[1]}



