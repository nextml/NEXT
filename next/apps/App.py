import numpy
import numpy.random
import json
import time
import traceback

from next.resource_client.ResourceClient import ResourceClient
import next.utils as utils
from next.apps.AppPrototype import AppPrototype
from next.apps.PoolBasedTripletMDS.dashboard.Dashboard import PoolBasedTripletMDSDashboard

class PoolBasedTripletMDS(AppPrototype):
    def __init__(self): 
        self.app_id = 'PoolBasedTripletMDS'

    def daemonProcess(self,exp_uid,args_json,db,ell):
        pass

    def initExp(self,exp_uid,args_json,db,ell):
        success, args, message = verifier(args_json):
        if not success:
            return False, "Failed to verify: {}".format(message)

        # remove any reminants of an experiment if it exists
        didSucceed,message = db.delete_docs_with_filter('experiments_admin',{'exp_uid':exp_uid})
        didSucceed,message = db.delete_docs_with_filter(app_id+':experiments',{'exp_uid':exp_uid})
        didSucceed,message = db.delete_docs_with_filter(app_id+':queries',{'exp_uid':exp_uid})
        didSucceed,message = db.delete_docs_with_filter(app_id+':participants',{'exp_uid':exp_uid})
        didSucceed,message = db.delete_docs_with_filter(app_id+':algorithms',{'exp_uid':exp_uid})
        
        didSucceed,message = ell.delete_logs_with_filter(app_id+':APP-CALL',{'exp_uid':exp_uid})
        didSucceed,message = ell.delete_logs_with_filter(app_id+':APP-RESPONSE',{'exp_uid':exp_uid})
        didSucceed,message = ell.delete_logs_with_filter(app_id+':APP-EXCEPTION',{'exp_uid':exp_uid})
        didSucceed,message = ell.delete_logs_with_filter(app_id+':ALG-DURATION',{'exp_uid':exp_uid})
        didSucceed,message = ell.delete_logs_with_filter(app_id+':ALG-EVALUATION',{'exp_uid':exp_uid})
        
        # add indexes (only adds them if they do not already exist)
        didSucceed,message = db.ensure_index('experiments_admin',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':experiments',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':queries',{'query_uid':1})
        didSucceed,message = db.ensure_index(app_id+':queries',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':queries',{'alg_uid':1})
        didSucceed,message = db.ensure_index(app_id+':queries',{'participant_uid':1})
        didSucceed,message = db.ensure_index(app_id+':participants',{'participant_uid':1})
        didSucceed,message = db.ensure_index(app_id+':participants',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':algorithms',{'alg_uid':1})
        didSucceed,message = db.ensure_index(app_id+':algorithms',{'exp_uid':1})

        didSucceed,message = ell.ensure_index(app_id+':APP-CALL',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-CALL',{'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-CALL',{'exp_uid':1,'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-CALL',{'exp_uid':1,'task':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-RESPONSE',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-RESPONSE',{'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-RESPONSE',{'exp_uid':1,'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-RESPONSE',{'exp_uid':1,'task':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-EXCEPTION',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-EXCEPTION',{'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-EXCEPTION',{'exp_uid':1,'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':APP-EXCEPTION',{'exp_uid':1,'task':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'alg_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'exp_uid':1,'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'alg_uid':1,'task':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-EVALUATION',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-EVALUATION',{'alg_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-EVALUATION',{'timestamp':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-EVALUATION',{'exp_uid':1,'timestamp':1})
        
        db.set('experiments_admin',exp_uid,'exp_uid',exp_uid)
        db.set('experiments_admin',exp_uid,'app_id',app_id)
        db.set('experiments_admin',exp_uid,'start_date',utils.datetime2str(utils.datetimeNow()))

        log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':args_json,'timestamp':utils.datetimeNow() } 
        ell.log( app_id+':APP-CALL', log_entry  )

        
  def getQuery(self,exp_uid,args_json,db,ell):
      pass

  def processAnswer(self,exp_uid,args_json,db,ell):
      pass

  def predict(self,exp_uid,args_json,db,ell):
      pass

  def getStats(self,exp_uid,args_json,db,ell):
      pass

    
