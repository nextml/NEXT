# TODO:
# x change the algorithm definitions. Done for LilUCB only
# o explore the dashboard, see what you need to change
# ? modify the widgets?
import json
import numpy
import next.apps.SimpleTargetManager
import next.utils as utils


class MyApp:
    def __init__(self,db):
        self.app_id = 'DuelingBanditsPureExploration'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):
        """
        This function is meant to store an additional components in the
        databse.

        In the implementation of two apps, DuelingBanditsPureExploration and
        PoolBasedTripletMDS, we only managed targets in this function. We
        stored the targets to the database than deleted the 'targets' key
        from args, replacing it with ``args['n']`` to
        represent a list of n targets. This is easier when doing numerical
        computation.

        Inputs
        ------
        exp_uid : The unique identifier to represent an experiment.
        args : The keys specified in the app specific YAML file in the
                   initExp section.
        butler : The wrapper for database writes. See next/apps/Butler.py for
                 more documentation.

        Returns
        -------
        args: The experiment data, potentially modified.
        """
        # TODO: change this in every app type coded thus far!
        if 'targetset' in args['targets'].keys():
            n = len(args['targets']['targetset'])
            self.TargetManager.set_targetset(butler.exp_uid, args['targets']['targetset'])
        else:
            n = args['targets']['n']
        args['n'] = n
        del args['targets']

        alg_data = {}
        algorithm_keys = ['n', 'failure_probability']
        for key in algorithm_keys:
            alg_data[key] = args[key]

        init_algs(alg_data)
        return args

    def getQuery(self, butler, alg, args):
        alg_response = alg({'participant_uid':args['participant_uid']})
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

        #DELETE
        # butler.memory.set('ketesting', 'value')
        # utils.debug_print('set done')
        # l = butler.memory.lock('asd')
        # utils.debug_print('lock object got')
        # l.acquire()
        # utils.debug_print('lock acquired')
        # for i in range(10000):
        #     utils.debug_print('a')
        # utils.debug_print('lock releasing')
        # l.release()
        # utils.debug_print('lock released')
        #END DELETE
        
        #if 'labels' in experiment_dict['args']['rating_scale']:
            #labels = experiment_dict['args']['rating_scale']['labels']
            #return_dict.update({'labels':labels})

        if 'context' in experiment_dict['args'] and 'context_type' in experiment_dict['args']:
            return_dict.update({'context':experiment_dict['args']['context'],'context_type':experiment_dict['args']['context_type']})

        return return_dict

    def processAnswer(self, butler, alg, args):
        #DELETE
        # a = butler.memory.get('ketesting')
        # assert a == 'value'
        # utils.debug_print("butler.memory testing: ", a)
        #END DELETE
        query = butler.queries.get(uid=args['query_uid'])
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'left':
                left_id = target['target']['target_id']
            if target['label'] == 'right':
                right_id = target['target']['target_id']
            if target['flag'] == 1:
                painted_id = target['target']['target_id']
                
        winner_id = args['target_winner']
        butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        alg({'left_id':left_id, 
             'right_id':right_id, 
             'winner_id':winner_id,
             'painted_id':painted_id})
        return {'winner_id':winner_id}
                

    def getModel(self, butler, alg, args):
        scores, precisions = alg()
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


    def format_responses(self, responses):
        formatted = []
        for response in responses:
            targets = {'target_' + target['label']: target['target']['primary_description']
                       for target in response['target_indices']}
            if 'winner_id' not in response:
                continue
            winner = {t['target']['target_id'] == response['winner_id']:
                    t['target']['primary_description']
                      for t in response['target_indices']}
            response.update({'target_winner': winner[True]})

            for key in ['q', '_id', 'target_indices', 'winner_id', 'context_type']:
                if key in response:
                    del response[key]
            response.update(targets)
            formatted += [response]

        return formatted

    def format_getModel_result(self, butler, alg, args):
        model = args['getModel_result']
        results = model['targets']
        target_keys_to_keep = ['primary_description', 'primary_type', 'alt_description', 'target_id']
        for result in results:
            target = result['target']
            result.update({key: target[key] for key in target_keys_to_keep})
            del result['target']
        return results
