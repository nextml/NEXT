import json
import numpy
import random
import numpy as np

import next.apps.SimpleTargetManager
import next.utils as utils
class CardinalBanditsFeatures(object):
    def __init__(self):
        self.app_id = 'CardinalBanditsFeatures'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()

    def initExp(self, exp_uid, exp_data, butler):
        """
        This function is meant to store any additional components in the
        databse.

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

            targetset = exp_data['args']['targets']['targetset']
            feature_filenames = exp_data['args']['feature_filenames']
            target_filenames = [im['alt_description'] for im in
                    targetset]

            new_target_idx = [feature_filenames.index(target)
                                        for  target in target_filenames]
            new_targetset = []
            utils.debug_print(exp_data['args'].keys())
            X = np.array(exp_data['args']['features'])
            for col, target in zip(new_target_idx,
                                   exp_data['args']['targets']['targetset']):
                target['feature_vector'] = X[:, col].tolist()
                new_targetset += [target]

            self.TargetManager.set_targetset(exp_uid, new_targetset)

            # old code, expanded by the for-loop above
            # self.TargetManager.set_targetset(exp_uid,
                            # [exp_data['args']['targets']['targetset'][i]
                                            # for i in new_target_idx])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['features']
        del exp_data['args']['targets']

        if 'labels' in exp_data['args']['rating_scale'].keys():
            labels = exp_data['args']['rating_scale']['labels']
            max_label = max( label['reward'] for label in labels )
            min_label = min( label['reward'] for label in labels )
            exp_data['args']['rating_scale']['R'] = max_label - min_label

        R = exp_data['args']['rating_scale']['R']
        alg_data = {'R':R}
        algorithm_keys = ['n','failure_probability']
        for key in algorithm_keys:
            alg_data[key]=exp_data['args'][key]

        return exp_data,alg_data

    def getQuery(self, exp_uid, experiment_dict, query_request, alg_response, butler):
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
        participant_doc = butler.participants.get(uid=query_request['args']['participant_uid'])
        if participant_doc['num_tries'] == 0:
            N = butler.experiment.get(key='args')['n']
            target_indices = random.sample(range(N),10) # 10 here means "show 10 random queries at the start"
            targets_list = [{'index':i,'target':self.TargetManager.get_target_item(exp_uid, i)} for i in target_indices]
            return_dict = {'initial_query':True,'targets':targets_list,'instructions':butler.experiment.get(key='args')['instructions']}
        else:
            target = self.TargetManager.get_target_item(exp_uid, alg_response)
            targets_list = [{'index':alg_response,'target':target}]

            init_index = butler.participants.get(uid=query_request['args']['participant_uid'],key="i_hat")
            init_target = self.TargetManager.get_target_item(exp_uid, init_index)

            return_dict = {'initial_query':False,'targets':targets_list,'main_target':init_target,'instructions':butler.experiment.get(key='args')['query_instructions']}

            if 'labels' in experiment_dict['args']['rating_scale']:
                labels = experiment_dict['args']['rating_scale']['labels']
                return_dict.update({'labels':labels})

                if 'context' in experiment_dict['args'] and 'context_type' in experiment_dict['args']:
                    return_dict.update({'context':experiment_dict['args']['context'],'context_type':experiment_dict['args']['context_type']})
        return return_dict

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
        participant_uid = query['participant_uid']
        participant_doc = butler.participants.get(uid=participant_uid)
        butler.participants.increment(uid=participant_uid, key='num_tries')
        if answer['args']['initial_query']:
            initial_arm = answer['args']['answer']['initial_arm']
            butler.participants.set(uid=participant_uid,key="i_hat",value=initial_arm)
            return {}, {'participant_doc': participant_doc}
        else:
            target_id = query['targets'][0]['target']['target_id']
            target_reward = answer['args']['answer']['target_reward']

            butler.participants.append(uid=participant_uid, key='do_not_ask_list', value=target_id)

            query_update = {'target_id':target_id,'target_reward':target_reward}

            alg_args_dict = {'target_id':target_id,
                             'target_reward':target_reward,
                             'participant_doc': participant_doc}

        return query_update, alg_args_dict

    def getModel(self, exp_uid, alg_response, args_dict, butler):
        scores, precisions = alg_response
        ranks = (-numpy.array(scores)).argsort().tolist()
        n = len(scores)
        indexes = numpy.array(range(n))[ranks]
        scores = numpy.array(scores)[ranks]
        precisions = numpy.array(precisions)[ranks]
        ranks = range(n)

        targets = []
        for index in range(n):
          targets.append( {'index':indexes[index],
                           'target':self.TargetManager.get_target_item(exp_uid, indexes[index]),
                           'rank':ranks[index],
                           'score':scores[index],
                           'precision':precisions[index]} )
        num_reported_answers = butler.experiment.get('num_reported_answers')
        return {'targets': targets, 'num_reported_answers':num_reported_answers} 
        
    def getStats(self, exp_uid, stats_request, dashboard, butler):
        """
        Get statistics to display on the dashboard.
        """
        stat_id = stats_request['args']['stat_id']
        task = stats_request['args']['params'].get('task', None)
        alg_label = stats_request['args']['params'].get('alg_label', None)
        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                     'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                     'compute_duration_detailed_stacked_area_plot':dashboard.compute_duration_detailed_stacked_area_plot,
                     'response_time_histogram':dashboard.response_time_histogram,
                     'network_delay_histogram':dashboard.network_delay_histogram,
                     'most_current_ranking':dashboard.most_current_ranking}

        default = [self.app_id, exp_uid]
        args = {'api_activity_histogram':default + [task],
                'compute_duration_multiline_plot':default + [task],
                'compute_duration_detailed_stacked_area_plot':default + [task, alg_label],
                'response_time_histogram':default + [alg_label],
                'network_delay_histogram':default + [alg_label],
                'most_current_ranking':default + [alg_label]}
        return functions[stat_id](*args[stat_id])

