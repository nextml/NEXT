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

    def processAnswer(self, exp_uid, args_json, db, ell):
        pass
    def getStats(self, exp_uid, args_json, db, ell):
        pass
    def predict(self, exp_uid, args_json, db, ell):
        pass
