import json
import numpy
import numpy as np
import next.apps.SimpleTargetManager
import next.utils as utils

class MyApp:
    def __init__(self,db):
        self.app_id = 'CardinalBanditsPureExploration'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):
        """
        This function is meant to store any additional components in the
        databse.

        Inputs
        ------
        exp_uid : The unique identifier to represent an experiment.
        args : The keys specified in the app specific YAML file in the
                   initExp section.
        butler : The wrapper for database writes. See next/apps/Butler.py for
                 more documentation.

        Returns
        -------
        exp_data: The experiment data, potentially modified.
        """
        if 'targetset' in args['targets'].keys():
            n  = len(args['targets']['targetset'])
            self.TargetManager.set_targetset(butler.exp_uid, args['targets']['targetset'])
        else:
            n = args['targets']['n']
        args['n'] = n
        del args['targets']

        if 'labels' in args['rating_scale'].keys():
            labels = args['rating_scale']['labels']
            max_label = max( label['reward'] for label in labels )
            min_label = min( label['reward'] for label in labels )
            args['rating_scale']['R'] = max_label-min_label

        R = args['rating_scale']['R']
        alg_data = {'R':R}
        algorithm_keys = ['n','failure_probability']
        for key in algorithm_keys:
            alg_data[key]=args[key]

        init_algs(alg_data)
        return args

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


    def format_responses(self, responses):
        formatted = []
        for response in responses:
            reward = {response['target_reward'] == l['reward']: l['label']
                      for l in response['labels']}
            reward_num = {response['target_reward'] == l['reward']: l['reward']
                      for l in response['labels']}
            target = response['target_indices'][0]['target']['primary_description']
            response.update({'target': target, 'target_reward_label': reward[True],
                'target_reward': reward_num[True]})

            for key in ['_id', 'target_indices',
                        'context_type', 'labels', 'target_id']:
                if key in response:
                    del response[key]
            formatted += [response]

        return formatted


