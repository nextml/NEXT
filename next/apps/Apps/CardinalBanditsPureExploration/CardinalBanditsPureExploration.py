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

    def getQuery(self, butler, alg, args):
        participant_uid = args.get('participant_uid', butler.exp_uid)
        alg_response = alg({'participant_uid':participant_uid})
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

    def processAnswer(self, butler, alg, args):
        query = butler.queries.get(uid=args['query_uid'])
        target_id = query['target_indices'][0]['target']['target_id']
        target_reward = args['target_reward']
        alg({'target_id':target_id,'target_reward':target_reward})
        return {'target_id':target_id,'target_reward':target_reward}

    def getModel(self, butler, alg, args):
        alg_response = alg()
        scores, precisions,counts = alg_response
        ranks = (-numpy.array(scores)).argsort().tolist()
        n = len(scores)
        indexes = numpy.array(range(n))[ranks]
        scores = numpy.array(scores)[ranks]
        precisions = numpy.array(precisions)[ranks]
        counts = numpy.array(counts)[ranks]
        standard_deviations = precisions*numpy.sqrt(counts)
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
                                 'precision':precisions[index],
                                 'standard_deviation':standard_deviations[index],
                                 'count':counts[index]} )
        else:
            for index in range(n):
                targets.append( {'index':indexes[index],
                                 'target':target_set[indexes[index]],
                                 'rank':ranks[index],
                                 'score':scores[index],
                                 'precision':precisions[index],
                                 'standard_deviation':standard_deviations[index],
                                 'count':counts[index]} )
        return {'targets': targets} 
        
