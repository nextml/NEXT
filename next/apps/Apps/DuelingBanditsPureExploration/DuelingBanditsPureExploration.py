# TODO:
# o implement the functions below.
# o change the algorithm definitions (and what they return?)
# o look at diffs
# o explore the dashboard, see what you need to change
# - look at the butler code. Butler is another database wrapper
# x modify the tests to delete exp_key
# x check if daemonProcess still needed (I don't think it is)
# x Implement the .yaml file
#   modify the widgets?

class DuelingBanditsPureExploration(object):
    def __init__(self):
        self.app_id = 'DuelingBanditsPureExploration'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()

    def initExp(self, exp_uid, args_json, db, ell):
        if 'targetset' in exp_data['args']['targets'].keys():
            n  = len(exp_data['args']['targets']['targetset'])
            self.TargetManager.set_targetset(exp_data['args']['targets']['targetset'])
        else:
            n = exp_data['args']['targets']['n']
        exp_data['args']['n'] = n
        del exp_data['args']['targets']
        return exp_data

    def getQuery(self, exp_uid, query_request, alg_response, butler):
        targets = [self.TargetMapper.get_target_item(exp_uid, alg_response[i])
                                                 for i in [0, 1, 2]]

        targets_dict = [{'index':index_left,'label':'left'}, 
                        {'index':index_right,'label':'right'}]

        if targets[0] == targets[-1]:
            targets_dict[0]['flag'] = 1
            targets_dict[0]['flag'] = 0
        else:
            targets_dict[0]['flag'] = 0
            targets_dict[0]['flag'] = 1

        return {'target_indices':targets_dict}

    def processAnswer(self, exp_uid, query, answer, butler):
        pass
    def getStats(self, exp_uid, alg_response, args_dict):
        pass
    def getModel(self, exp_uid, stats_requst, dashboard, butler):
        pass
