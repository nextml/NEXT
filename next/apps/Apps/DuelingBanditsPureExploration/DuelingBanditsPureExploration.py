# TODO:
# x change the algorithm definitions. Done for LilUCB only
# o explore the dashboard, see what you need to change
# ? modify the widgets?
import json
import numpy

import next.apps.SimpleTargetManager
import next.utils as utils
class DuelingBanditsPureExploration(object):
    def __init__(self,db):
        self.app_id = 'DuelingBanditsPureExploration'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, exp_data):
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
        # TODO: change this in every app type coded thus far!
        if 'targetset' in exp_data['args']['targets'].keys():
            n = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(butler.exp_uid, exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']

        alg_data = {}
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
        targets = [self.TargetManager.get_target_item(butler.exp_uid, alg_response[i])
                                                 for i in [0, 1, 2]]

        targets_list = [{'target':targets[0],'label':'left'}, 
                        {'target':targets[1],'label':'right'}]


        if targets[0]['target_id'] == targets[-1]['target_id']:
            targets_list[0]['flag'] = 1
            targets_list[1]['flag'] = 0
        else:
            targets_list[0]['flag'] = 0
            targets_list[1]['flag'] = 1

        return_dict = {'target_indices':targets_list}

        experiment_dict = butler.experiment.get()

        #if 'labels' in experiment_dict['args']['rating_scale']:
            #labels = experiment_dict['args']['rating_scale']['labels']
            #return_dict.update({'labels':labels})

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
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'left':
                left_id = target['target']['target_id']
            if target['label'] == 'right':
                right_id = target['target']['target_id']
            if target['flag'] == 1:
                painted_id = target['target']['target_id']
                
        winner_id = answer['args']['target_winner']
        butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        query_update = {'winner_id':winner_id}
        algs_args_dict = {'left_id':left_id, 
                        'right_id':right_id, 
                        'winner_id':winner_id,
                        'painted_id':painted_id}
        return query_update,algs_args_dict
                

    def getModel(self, butler, args_dict, alg_response):
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
                           'target':self.TargetManager.get_target_item(butler.exp_uid, indexes[index]),
                           'rank':ranks[index],
                           'score':scores[index],
                           'precision':precisions[index]} )
        num_reported_answers = butler.experiment.get('num_reported_answers')
        return {'targets': targets, 'num_reported_answers':num_reported_answers} 


