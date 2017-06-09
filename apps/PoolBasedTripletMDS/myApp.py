import json
import next.utils as utils
import next.apps.SimpleTargetManager

class MyApp:
    def __init__(self,db):
        self.app_id = 'PoolBasedTripletMDS'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):
        exp_uid = butler.exp_uid
        if 'targetset' in args['targets'].keys():
            n  = len(args['targets']['targetset'])
            self.TargetManager.set_targetset(exp_uid, args['targets']['targetset'])
        else:
            n = args['targets']['n']
        args['n'] = n
        del args['targets']

        alg_data = {}
        algorithm_keys = ['n','d','failure_probability']
        for key in algorithm_keys:
            if key in args:
                alg_data[key]=args[key]

        init_algs(alg_data)
        return args

    def getQuery(self, butler, alg, args):
        alg_response = alg()
        exp_uid = butler.exp_uid
        center  = self.TargetManager.get_target_item(exp_uid, alg_response[0])
        left  = self.TargetManager.get_target_item(exp_uid, alg_response[1])
        right  = self.TargetManager.get_target_item(exp_uid, alg_response[2])
        center['label'] = 'center'
        left['label'] = 'left'
        right['label'] = 'right'
        return {'target_indices':[center, left, right]}

    def processAnswer(self, butler, alg, args):
        query = butler.queries.get(uid=args['query_uid'])
        targets = query['target_indices']
        for target in targets:
            if target['label'] == 'center':
                center_id = target['target_id']
            elif target['label'] == 'left':
                left_id = target['target_id']
            elif target['label'] == 'right':
                right_id = target['target_id']
        target_winner = args['target_winner']
        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        n = experiment['args']['n']
        if num_reported_answers % ((n+4)/4) == 0:
            butler.job('getModel', json.dumps({'exp_uid':butler.exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        q = [left_id, right_id,center_id] if target_winner==left_id else [right_id, left_id,center_id]

        alg({'left_id':left_id, 'right_id':right_id, 'center_id':center_id, 'target_winner':target_winner})
        return {'target_winner':target_winner, 'q':q}

    def getModel(self, butler, alg, args):
        return alg()

    def format_responses(self, responses):
        formatted = []
        for response in responses:
            if 'target_winner' not in response:
                continue
            targets = {'target_' + target['label']: target['primary_description']
                       for target in response['target_indices']}
            winner = {t['target_id'] == response['target_winner']: t['primary_description']
                      for t in response['target_indices']}
            response.update({'target_winner': winner[True]})

            for key in ['q', '_id', 'target_indices']:
                if key in response:
                    del response[key]
            response.update(targets)
            formatted += [response]

        return formatted

    def format_getModel_result(self, butler, alg, args):
        model = args['getModel_result']
        utils.debug_print(model)
        X = model['X']
        targets = self.TargetManager.get_targetset(butler.exp_uid)
        utils.debug_print('targets[0]', targets[0])
        if len(X) != len(targets):
            raise ValueError('Not same number of targets and embedding points')
        for i, x in enumerate(X):
            d = {'x_'+str(j): xj for j, xj in enumerate(x)}
            targets[i].update(d)

        to_remove = ['primary_type', 'alt_type', 'exp_uid', '_id']
        targets = utils.remove_keys_from_targets(to_remove, targets)

        return targets
