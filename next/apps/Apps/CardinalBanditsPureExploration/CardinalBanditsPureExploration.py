import json
import numpy
import next.apps.SimpleTargetManager
import next.utils as utils

class CardinalBanditsPureExploration(object):
    def __init__(self,db):
        self.app_id = 'CardinalBanditsPureExploration'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, exp_data):
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
            self.TargetManager.set_targetset(butler.exp_uid, exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']

        if 'labels' in exp_data['args']['rating_scale'].keys():
            labels = exp_data['args']['rating_scale']['labels']
            max_label = max( label['reward'] for label in labels )
            min_label = min( label['reward'] for label in labels )
            exp_data['args']['rating_scale']['R'] = max_label-min_label

        R = exp_data['args']['rating_scale']['R']
        alg_data = {'R':R}
        algorithm_keys = ['n','failure_probability']
        for key in algorithm_keys:
            alg_data[key]=exp_data['args'][key]

        return exp_data,alg_data

    def getQuery(self, butler, query_request, alg_response):
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
        participant_uid = query_request['args'].get('participant_uid', query_request['exp_uid'])
        butler.participants.append(uid=participant_uid,key='do_not_ask_list',value=alg_response)

        target = self.TargetManager.get_target_item(butler.exp_uid, alg_response)
        targets_list = [{'target':target}]

        return_dict = {'target_indices':targets_list}
        experiment_dict = butler.experiment.get()
        if 'labels' in experiment_dict['args']['rating_scale']:
            labels = experiment_dict['args']['rating_scale']['labels']
            return_dict.update({'labels':labels})

        if 'context' in experiment_dict['args'] and 'context_type' in experiment_dict['args']:
            return_dict.update({'context':experiment_dict['args']['context'],'context_type':experiment_dict['args']['context_type']})

        return return_dict

    def processAnswer(self, butler, query, answer):
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
        target_id = query['target_indices'][0]['target']['target_id']     
        target_reward = answer['args']['target_reward']

        query_update = {'target_id':target_id,'target_reward':target_reward}
        alg_args_dict = {'target_id':target_id,'target_reward':target_reward}
        return query_update,alg_args_dict

    def getModel(self, butler, args_dict, alg_response):
        scores, precisions = alg_response
        ranks = (-numpy.array(scores)).argsort().tolist()
        n = len(scores)
        indexes = numpy.array(range(n))[ranks]
        scores = numpy.array(scores)[ranks]
        precisions = numpy.array(precisions)[ranks]
        ranks = range(n)
        target_set = self.TargetManager.get_targetset(butler.exp_uid)
        target_set = sorted(target_set,key=lambda x: x['target_id'])
        targets = []
        if len(target_set)==0:
            for index in range(n):
                targets.append( {'index':indexes[index],
                               'target':{'target_id':indexes[index],
                                          'primary_description':str(indexes[index]),
                                          'primary_type':'text',
                                          'alt_description':str(indexes[index]),
                                          'alt_type':'text'},
                               'rank':ranks[index],
                               'score':scores[index],
                               'precision':precisions[index]} )
        else:
            for index in range(n):
                targets.append( {'index':indexes[index],
                               'target':target_set[indexes[index]],
                               'rank':ranks[index],
                               'score':scores[index],
                               'precision':precisions[index]} )
        return {'targets': targets} 
        
