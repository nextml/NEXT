# TODO:
# x implement the functions below.
# x change the algorithm definitions. Done for LilUCB only
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
        """
        This function is meant to store an additional components in the
        databse.

        In the implementation of two apps, DuelingBanditsPureExploration and
        PoolBasedTripletMDS, we only managed targets in this function. We
        stored the targets to the database than deleted the 'targets' key
        from exp_data, replacing it with ``exp_data['args']['n']`` to
        represent a list of n targets. This is easier when doing numerical
        computation.

        Inputs
        ------
        exp_uid : The unique identifier to represent an experiment.
        exp_data : The keys specified in the app specific YAML file in the
                   initExp section.
        butler : The wrapper for database writes. See next/apps/Butler.py for
                 more documentation.

        Returns
        -------
        exp_data: The experiment data, potentially modified.
        """
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']
        return exp_data

    def getQuery(self, exp_uid, query_request, alg_response, butler):
        """
        The function that gets the next query, given a query reguest and
        algorithm response.

        Inputs
        ------
        exp_uid : The unique identiefief for the exp.
        query_request :
        alg_response : The response from the algorithm. The algorithm should
                       return only one value, be it a list or a dictionary.
        butler : The wrapper for database writes. See next/apps/Butler.py for
                 more documentation.

        Returns
        -------
        A dictionary with a key ``target_indices``.

        TODO: Document this further
        """
        targets = [self.TargetManager.get_target_item(exp_uid, alg_response[i])
                                                 for i in [0, 1, 2]]

        targets_dict = [{'index':targets[0],'label':'left'}, 
                        {'index':targets[1],'label':'right'}]

        if targets[0] == targets[-1]:
            targets_dict[0]['flag'] = 1
            targets_dict[1]['flag'] = 0
        else:
            targets_dict[0]['flag'] = 0
            targets_dict[1]['flag'] = 1

        return {'target_indices':targets_dict}

    def processAnswer(self, exp_uid, query, answer, butler):
        """
        Parameters
        ----------
        exp_uid : The experiments unique ID.
        query :
        answer: 
        butler : 

        Returns
        -------
        dictionary with keys:
            alg_args: Keywords that are passed to the algorithm.
            query_update :

        For example, this function might return ``{'a':1, 'b':2}``. The
        algorithm would then be called with
        ``alg.processAnswer(butler, a=1, b=2)``
        """
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'left':
                left_id = target['index']
            if target['label'] == 'right':
                right_id = target['index']
            if target['flag'] == 1:
                painted_id = target['index']
                
        winner_id = answer['args']['target_winner']

        experiment = butler.experiment.get()
        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        n = experiment['args']['n']
        if num_reported_answers % ((n+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))

        #query = {'query_uid':None, 'targets':targets,
                 #'context_type':experiment['args']['context_type'],
                 #'context':experiment['args']['context']}
        #query = {}
        q = [left_id, right_id] if winner_id==left_id else [right_id, left_id]
        

        return {'alg_args':{'left_id':left_id, 
                            'right_id':right_id, 
                            'winner_id':winner_id,
                            'painted_id':painted_id},
                'query_update':{'winner_id':winner_id, 'q':query}}
        

    def getStats(self, exp_uid, stats_request, dashboard, butler):
        """
        Get statistics to display on the dashboard.
        """
        stat_id = stats_request['args']['stat_id']
        task = stats_request['args']['params'].get('task', None)
        alg_label = stats_request['args']['params'].get('alg_label', None)

        common_panels = 
        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                'api_processAnswer_activity_stacked_histogram':dashboard.api_processAnswer_activity_stacked_histogram,
                'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                'compute_duration_detailed_stacked_area_plot':dashboard.compute_duration_detailed_stacked_area_plot,
                'response_time_histogram':dashboard.response_time_histogram,
                'network_delay_histogram':dashboard.network_delay_histogram,
                'most_current_ranking':dashboard.most_current_ranking
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
