import next.utils as utils
import next.apps.SimpleTargetManager
import json
from next.resource_client.ResourceClient import ResourceClient

class PoolBasedTripletMDS(object):
    def __init__(self):
        self.app_id = 'PoolBasedTripletsMDS'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager()
        
    def initExp(self, exp_uid, args_dict, db, ell):
        if 'targetset' in args_dict['args']['targets'].keys():
            n  = len(args_dict['args']['targets']['targetset'])
            self.TargetManager.set_targetset(args_dict['args']['targets']['targetset'])
        else:
            n = args_dict['args']['targets']['n']
        args_dict['args']['n'] = n
        del args_dict['args']['targets']
        return args_dict
    def getQuery(self, exp_uid, args_dict, alg_response, db, ell):
        index_center, index_left, index_right, dt = alg_response
        # create JSON query payload
        query = {}
        query['target_indices'] = [ {'target':self.TargetManager.get_target_item(index_center),'label':'center'},
                                    {'target':self.TargetManager.get_target_item(index_left),'label':'left'},
                                    {'target':self.TargetManager.get_target_item(index_right),'label':'right'} ]
        return query

    def processAnswer(self, exp_uid, args_dict, num_reported_answers, db):
        targets, didSucceed, message = db.get(self.app_id+':queries',args_dict['query_uid'],'target_indices')
        for target in targets:
            if target['label'] == 'center':
                center_id = target['target_id']
            elif target['label'] == 'left':
                left_id = target['target_id']
            elif target['label'] == 'right':
                right_id = target['target_id']
        target_winner = args_dict['target_winner']
        # update query doc
        db.set(self.app_id+':queries',args_dict['query_uid'],'target_winner',target_winner)

        q = [left_id, right_id, center_id]

        if target_winner==right_id:
            q = [right_id,left_id,center_id]
        db.set(self.app_id+':queries',args_dict['query_uid'],'q',q)
        # check if we're going to evaluate this loss
        n, _, _ = db.get(self.app_id+':experiments',exp_uid,'n')

        # make a predict call ~ every n/4 queries     
        if num_reported_answers % ((n+4)/4) == 0:
            predict_id = 'get_embedding'
            params = {'alg_label':alg_label}
            predict_args_dict = {'predict_id':predict_id,'params':params}
            predict_args_json = json.dumps(predict_args_dict)
            db.submit_job(self.app_id,
                          exp_uid,
                          'predict',
                          predict_args_json,
                          ignore_result=True)
            
        
        return {'left_id':left_id, 'right_id':right_id,
                'center_id':center_id, 'target_winner':target_winner}

    def getStats(self, stat_id, params, dashboard):
        # input task
        task = params['task']
        alg_label = params['alg_label']

        # These are the functions corresponding to stat_id
        functions = {'api_activity_histogram':dashboard.api_activity_histogram,
                     'api_processAnswer_activity_stacked_histogram':dashboard.api_processAnswer_activity_stacked_histogram,
                     'compute_duration_multiline_plot':dashboard.compute_duration_multiline_plot,
                     'compute_duration_detailed_stacked_area_plot':dashboard.compute_duration_detailed_stacked_area_plot,
                     'response_time_histogram':dashboard.response_time_histogram,
                     'network_delay_histogram':network_delay_histogram,
                     'most_current_ranking':most_current_ranking
                    }

        # TODO: Scott, please explain to me. I don't get it.
        # These are the args passed into that function
        default = [self.app_id, exp_uid]
        args = {'api_activity_histogram':default  + [task],
                'api_processAnswer_activity_stacked_histogram':default,
                'compute_duration_multiline_plot':default + [task],
                'compute_duration_detailed_stacked_area_plot':default + [task, alg_label],
                'response_time_histogram':default + [alg_label],
                'network_delay_histogram':default + [alg_label],
                'most_current_ranking':default + [alg_label]
                }

        # this line call the function specified by stat_id with the arguments
        # for stat_id. Dictionaries are replacements for if-statements and below
        # line unpacks some statements
        return functions[stat_id](*args[stat_id])

    def predict(self, exp_uid, alg, args_dict, db):
        predict_id = args_dict['predict_id']
        meta = {}
        if predict_id=='get_embedding':
            ##### Get Embedding #####
            Xd,num_reported_answers,dt = utils.timeit(alg.predict)(rc)

            log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'predict','duration':dt }
            log_entry_durations.update( rc.getDurations() )
            meta = {'log_entry_durations':log_entry_durations}

            params['Xd'] = Xd
            params['num_reported_answers'] = num_reported_answers

            log_entry = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'timestamp':utils.datetimeNow() }
            log_entry.update( params )

            ell.log(self.app_id+':ALG-EVALUATION', log_entry  )

            params['timestamp'] = str(log_entry['timestamp'])
            response_args_dict = params

        elif predict_id=='get_queries':

            # get list of triplets from test
            queries,didSucceed,message = db.get_docs_with_filter(self.app_id+':queries',{'alg_uid':alg_uid})

            S = []
            for query in queries:
                if 'q' in query.keys():
                    q = query['q']
                    S.append(q)

            params['queries'] = S
            params['num_reported_answers'] = len(S)
            response_args_dict = params

        return response_args_dict, meta
