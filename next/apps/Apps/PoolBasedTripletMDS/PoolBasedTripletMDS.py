import next.utils as utils

class PoolBasedTripletMDS(object):
    def initExp(self, exp_uid, args_json, db, ell):
        pass
    def getQuery(self, exp_uid, args_uid, alg_response):
        index_center,index_left,index_right,dt = alg_response

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

    def processAnswer(self, app_id, args_dict, query_uid, db):
        targets, didSucceed, message = db.get(app_id+':queries',query_uid,'target_indices')

        for target in targets:
            if target['label'] == 'center':
                index_center = target['index']
            elif target['label'] == 'left':
                index_left = target['index']
            elif target['label'] == 'right':
                index_right = target['index']

        index_winner = args_dict['index_winner']

        # update query doc
        timestamp_query_generated,didSucceed,message = db.get(app_id+':queries',query_uid,'timestamp_query_generated')
        datetime_query_generated = utils.str2datetime(timestamp_query_generated)
        timestamp_answer_received = args_dict.get('meta',{}).get('timestamp_answer_received',None)

        if timestamp_answer_received == None:
            datetime_answer_received = datetime_query_generated
        else:
            datetime_answer_received = utils.str2datetime(timestamp_answer_received)

        delta_datetime = datetime_answer_received - datetime_query_generated
        round_trip_time = delta_datetime.seconds + delta_datetime.microseconds/1000000.
        response_time = float(args_dict.get('response_time',0.))
        db.set(app_id+':queries',query_uid,'response_time',response_time)
        db.set(app_id+':queries',query_uid,'network_delay',round_trip_time-response_time)
        db.set(app_id+':queries',query_uid,'index_winner',index_winner)

        q = [index_left, index_right, index_center]

        if index_winner==index_right:
            q = [index_right,index_left,index_center]

        db.set(app_id+':queries',query_uid,'q',q)

        log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'processAnswer','duration':dt }
        log_entry_durations.update( rc.getDurations() )
        meta = {'log_entry_durations':log_entry_durations}

        # check if we're going to evaluate this loss
        n, _, _ = db.get(app_id+':experiments',exp_uid,'n')

        if num_reported_answers % ((n+4)/4) == 0:
            predict_id = 'get_embedding'
            params = {'alg_label':alg_label}
            predict_args_dict = {'predict_id':predict_id,'params':params}
            predict_args_json = json.dumps(predict_args_dict)

                db.submit_job(app_id,exp_uid,'predict',predict_args_json,ignore_result=True)

        return {'index_left'index_left:, 'index_right':index_right,
                'index_center':index_center, 'index_winner':index_winner}, meta

    def getStats(self, exp_uid, args_json, db, ell):
        pass
    def predict(self, exp_uid, args_json, db, ell):
        pass
