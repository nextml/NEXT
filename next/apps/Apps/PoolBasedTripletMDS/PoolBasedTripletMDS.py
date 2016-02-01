import json
import next.utils as utils
import next.apps.SimpleTargetManager
from next.resource_client.ResourceClient import ResourceClient

class PoolBasedTripletMDS(object):
    def __init__(self):
        self.app_id = 'PoolBasedTripletMDS'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()

    def initExp(self, exp_uid, exp_data, db):
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']
        return exp_data

    def getQuery(self, exp_uid, query_request, alg_response, db):
        center  = self.TargetManager.get_target_item(exp_uid, alg_response[0])
        left  = self.TargetManager.get_target_item(exp_uid, alg_response[1])
        right  = self.TargetManager.get_target_item(exp_uid, alg_response[2])
        center['label'] = 'center'
        left['label'] = 'left'
        right['label'] = 'right'
        return {'target_indices':[center, left, right]}

    def processAnswer(self, exp_uid, query, answer, db):
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
        experiment,didSucceed,message = db.get_doc(self.app_id+':experiments', exp_uid)
        num_reported_answers, didSucceed, message = db.increment(self.app_id + ':experiments', exp_uid, 'num_reported_answers_for_' + query['alg_label'])
        n = experiment['args']['n']
        if True:#num_reported_answers % ((n+4)/4) == 0:
            getModel_args_dict = {'exp_uid':exp_uid,'args':{'alg_label':query['alg_label']}}
            db.submit_job(self.app_id,
                          exp_uid,
                          'getModel',
                          json.dumps(getModel_args_dict),
                          ignore_result=True)
        return {'alg_args':{'left_id':left_id, 'right_id':right_id, 'center_id':center_id, 'target_winner':target_winner},
                'query_update':{'target_winner':target_winner}}

    def getModel(self, exp_uid, alg_response, args_dict, db):
        return alg_response

    def getStats(self, stat_id, params, dashboard):
        task = params['task']
        alg_label = params['alg_label']

        # These are the functions corresponding to stat_id
        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                     'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                     'compute_duration_detailed_stacked_area_plot':dashboard.compute_duration_detailed_stacked_area_plot,
                     'response_time_histogram':dashboard.response_time_histogram,
                     'network_delay_histogram':dashboard.network_delay_histogram,
                     'most_current_ranking':dashboard.most_current_ranking}

        # TODO: Scott, please explain to me. I don't get it.
        # These are the args passed into that function
        default = [self.app_id, exp_uid]
        args = {'api_activity_histogram':default + [task],
                'compute_duration_multiline_plot':default + [task],
                'compute_duration_detailed_stacked_area_plot':default + [task, alg_label],
                'response_time_histogram':default + [alg_label],
                'network_delay_histogram':default + [alg_label],
                'most_current_ranking':default + [alg_label]}

        # this line call the function specified by stat_id with the arguments
        # for stat_id. Dictionaries are replacements for if-statements and below
        # line unpacks some statements
        return functions[stat_id](*args[stat_id])

 
