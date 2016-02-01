import next.utils as utils
import next.apps.SimpleTargetManager
import json
from next.resource_client.ResourceClient import ResourceClient

class PoolBasedTripletMDS(object):
    def __init__(self):
        self.app_id = 'PoolBasedTripletMDS'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()

    def initExp(self, exp_uid, args_dict, db, ell):
        if 'targetset' in args_dict['args']['targets'].keys():
            n  = len(args_dict['args']['targets']['targetset'])
            self.TargetManager.set_targetset(args_dict['args']['targets']['targetset'])
        else:
            n = args_dict['args']['targets']['n']
        args_dict['args']['n'] = n
        del args_dict['args']['targets']
        return args_dict
    
    def getQuery(self, exp_uid, args_dict, alg_response, db, ell):
        target_id_center, target_id_left, target_id_right, dt = alg_response
        # create JSON query payload
        query = {}
        print '\n'*5 + 'here myAPp 70'
        center  = self.TargetManager.get_target_item(exp_uid, target_id_center)
        left  = self.TargetManager.get_target_item(exp_uid, target_id_left)
        right  = self.TargetManager.get_target_item(exp_uid, target_id_right)
        center['label'] = 'center'
        left['label'] = 'left'
        right['label'] = 'right'
        query['target_indices'] = [center, left, right]
        return query

    def processAnswer(self, exp_uid, args_dict, db):
        query, didSucceed, message = db.get_doc(self.app_id+':queries', args_dict['args']['query_uid'])
        targets = query['target_indices']
        alg_label = query['alg_label']
        for target in targets:
            if target['label'] == 'center':
                center_id = target['target_id']
            elif target['label'] == 'left':
                left_id = target['target_id']
            elif target['label'] == 'right':
                right_id = target['target_id']
        target_winner = args_dict['args']['target_winner']
        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment,didSucceed,message = db.get_doc(self.app_id+':experiments', exp_uid)
        num_reported_answers, didSucceed, message = db.increment(self.app_id + ':experiments', exp_uid, 'num_reported_answers_for_' + alg_label)
        n = experiment['args']['n']
        if num_reported_answers % ((n+4)/4) == 0:
            predict_args_dict = {'exp_uid':exp_uid,'args':{'alg_label':args_dict['args']['alg_label']}}
            db.submit_job(self.app_id,
                          exp_uid,
                          'getModel',
                          json.dumps(predict_args_dict),
                          ignore_result=True)
        return {'alg':{'left_id':left_id, 'right_id':right_id, 'center_id':center_id, 'target_winner':target_winner},
                'doc':{'target_winner':target_winner}}

    def getStats(self, stat_id, params, dashboard):
        # input task
        task = params['task']
        alg_label = params['alg_label']

        # These are the functions corresponding to stat_id
        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                     'api_processAnswer_activity_stacked_histogram':dashboard.api_processAnswer_activity_stacked_histogram,
                     'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                     'compute_duration_detailed_stacked_area_plot':dashboard.compute_duration_detailed_stacked_area_plot,
                     'response_time_histogram':dashboard.response_time_histogram,
                     'network_delay_histogram':network_delay_histogram,
                     'most_current_ranking':most_current_ranking
                    }

        # TODO: Scott, please explain to me. I don't get it.
        # These are the args passed into that function
        default = [self.app_id, exp_uid]
        args = {'api_activity_histogram':default  + [task],
                'api_processAnswer_activity_stacked_histogram':default,
                'compute_duration_multiline_plot':default + [task],
                'compute_duration_detailed_stacked_area_plot':default + [task, alg_label],
                'response_time_histogram':default + [alg_label],
                'network_delay_histogram':default + [alg_label],
                'most_current_ranking':default + [alg_label]
                }

        # this line call the function specified by stat_id with the arguments
        # for stat_id. Dictionaries are replacements for if-statements and below
        # line unpacks some statements
        return functions[stat_id](*args[stat_id])

    def getModel(self, exp_uid, alg_response, args_dict, db):
        return alg_response
