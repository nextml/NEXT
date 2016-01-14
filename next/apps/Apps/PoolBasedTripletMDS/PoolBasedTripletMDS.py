import next.utils as utils

class PoolBasedTripletMDS(object):
    def __init__(self):
        self.app_id = 'PoolBasedTripletsMDS'

    def initExp(self, exp_uid, args_json, db, ell):
        pass

    def getQuery(self, exp_uid, args_uid, alg_response):
        index_center, index_left, index_right, dt = alg_response

        log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'getQuery','duration':dt }
        log_entry_durations.update( rc.getDurations() )
        meta = {'log_entry_durations':log_entry_durations}

        # create JSON query payload
        timestamp = str(utils.datetimeNow())
        query_uid = utils.getNewUID()
        query = {}
        query['query_uid'] = query_uid
        query['target_indices'] = [ {'index':index_center,'label':'center','flag':0},{'index':index_left,'label':'left','flag':0},{'index':index_right,'label':'right','flag':0} ]
        return {'query':query, 'query_uid':query_uid, 'timestamp':timestamp}

    def processAnswer(self, args_dict, query_uid, db):
        targets, didSucceed, message = db.get(self.app_id+':queries',query_uid,'target_indices')

        for target in targets:
            if target['label'] == 'center':
                index_center = target['index']
            elif target['label'] == 'left':
                index_left = target['index']
            elif target['label'] == 'right':
                index_right = target['index']

        index_winner = args_dict['index_winner']

        # update query doc
        timestamp_query_generated,didSucceed,message = db.get(self.app_id+':queries',query_uid,'timestamp_query_generated')
        datetime_query_generated = utils.str2datetime(timestamp_query_generated)
        timestamp_answer_received = args_dict.get('meta',{}).get('timestamp_answer_received',None)

        if timestamp_answer_received == None:
            datetime_answer_received = datetime_query_generated
        else:
            datetime_answer_received = utils.str2datetime(timestamp_answer_received)

        delta_datetime = datetime_answer_received - datetime_query_generated
        round_trip_time = delta_datetime.seconds + delta_datetime.microseconds/1000000.
        response_time = float(args_dict.get('response_time',0.))
        db.set(self.app_id+':queries',query_uid,'response_time',response_time)
        db.set(self.app_id+':queries',query_uid,'network_delay',round_trip_time-response_time)
        db.set(self.app_id+':queries',query_uid,'index_winner',index_winner)

        q = [index_left, index_right, index_center]

        if index_winner==index_right:
            q = [index_right,index_left,index_center]

        db.set(self.app_id+':queries',query_uid,'q',q)

        log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'processAnswer','duration':dt }
        log_entry_durations.update( rc.getDurations() )
        meta = {'log_entry_durations':log_entry_durations}

        # check if we're going to evaluate this loss
        n, _, _ = db.get(self.app_id+':experiments',exp_uid,'n')

        if num_reported_answers % ((n+4)/4) == 0:
            predict_id = 'get_embedding'
            params = {'alg_label':alg_label}
            predict_args_dict = {'predict_id':predict_id,'params':params}
            predict_args_json = json.dumps(predict_args_dict)

                db.submit_job(self.app_id,exp_uid,'predict',predict_args_json,ignore_result=True)

        return {'index_left'index_left:, 'index_right':index_right,
                'index_center':index_center, 'index_winner':index_winner}, meta

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

    def predict(self, exp_uid, alg_id, predict_id, db):
        meta = {}
        if predict_id=='get_embedding':
            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(self.app_id,exp_uid,alg_uid,db)

            # get specific algorithm to make calls to
            alg = utils.get_app_alg(self.app_id, alg_id)

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
