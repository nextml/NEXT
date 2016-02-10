# TODO:
# x implement the functions below.
# - change the algorithm definitions. Done for LilUCB only
# o look at diffs
# o explore the dashboard, see what you need to change
# - look at the butler code. Butler is another database wrapper
# x modify the tests to delete exp_key
# x check if daemonProcess still needed (I don't think it is)
# x Implement the .yaml file
# ? modify the widgets?
import next.apps.SimpleTargetManager

class DuelingBanditsPureExploration(object):
    def __init__(self):
        self.app_id = 'DuelingBanditsPureExploration'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()

    def initExp(self, exp_uid, exp_data, butler):
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']
        return exp_data

    def getQuery(self, exp_uid, query_request, alg_response, butler):
        targets = [self.TargetManager.get_target_item(exp_uid, alg_response[i])
                                                 for i in [0, 1, 2]]

        targets_dict = [{'index':targets[0],'label':'left'}, 
                        {'index':targets[1],'label':'right'}]

        if targets[0] == targets[-1]:
            targets_dict[0]['flag'] = 1
            targets_dict[0]['flag'] = 0
        else:
            targets_dict[0]['flag'] = 0
            targets_dict[0]['flag'] = 1

        return {'target_indices':targets_dict}

    def processAnswer(self, exp_uid, query, answer, butler):
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'left':
                left_id = target['index']
            if target['label'] == 'right':
                right_id = target['index']
            if target['flag'] == 1:
                painted_id = target['index']
                
        target_winner = answer['args']['target_winner']

        experiment = butler.experiment.get()
        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        n = experiment['args']['n']
        if num_reported_answers % ((n+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))

        query = {'query_uid':query_uid, 'targets':targets_dict,
                 'context_type':experiment['args']['context_type'],
                 'context':experiment['args']['context']}

        return {'alg_args':{'left_id':left_id, 
                            'right_id':right_id, 
                            'target_winner':target_winner},
                'query_update':{'target_winner':target_winner, 'q':query}}
        

    def getStats(self, exp_uid, stats_request, dashboard, butler):
        stat_id = stats_request['args']['stat_id']
        task = stats_request['args']['params'].get('task', None)
        alg_label = stats_request['args']['params'].get('alg_label', None)

        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                'api_processAnswer_activity_stacked_histogram':dashboard.api_processAnswer_activity_stacked_histogram,
                'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                'compute_duration_detailed_stacked_area_plot':compute_duration_detailed_stacked_area_plot,
                'response_time_histogram':response_time_histogram,
                'network_delay_histogram':dashboard.network_delay_histogram,
                'most_current_ranking':most_current_ranking
                }

        default = [self.app_id, exp_uid]
        args = {'api_activity_histogram':default + [task],
                'api_processAnswer_activity_stacked_histogram':default,
                'compute_duration_multiline_plot':default + [task],
                'compute_duration_detailed_stacked_area_plot':default + [task, alg_label],
                'response_time_histogram':default + [alg_label],
                'network_delay_histogram':default + [alg_label],
                'most_current_ranking':default + [alg_label]
                }


        return functions[stat_id](*args)

    def getModel(self, exp_uid, alg_response, args_dict, butler):
        return {'num_reported_answers':alg_response[0]}
