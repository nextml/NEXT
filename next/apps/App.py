import numpy
import numpy.random
import json
import time
import traceback

from next.resource_client.ResourceClient import ResourceClient
import next.utils as utils
from next.apps.AppPrototype import AppPrototype
import next.apps.Verifier as Verifier
from next.apps.PoolBasedTripletMDS.dashboard.Dashboard import PoolBasedTripletMDSDashboard
import next.constants
git_hash = next.constants.GIT_HASH

class PoolBasedTripletMDS(AppPrototype):
    def __init__(self):
        self.app_id = 'PoolBasedTripletMDS'

    def daemonProcess(self,exp_uid,args_json,db,ell):
        pass

    def initExp(self,exp_uid,args_json,db,ell):
        try:
            app_id = self.app_id

            args_json, success, messages = Verifier.verify(args_json):
            if not success:
                # TODO: Turn this into an exception
                return False, "Failed to verify: {}".format(" \n".join(messages))

            # Convert the args JSON to an args dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = "%s.initExp input args_json is in improper format" % self.app_id
                return '{}', False, error

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

            # Database call that creates the experiment
            db.set('experiments_admin',exp_uid,'exp_uid',exp_uid)
            db.set('experiments_admin',exp_uid,'app_id',app_id)
            db.set('experiments_admin',exp_uid,'start_date',utils.datetime2str(utils.datetimeNow()))

            log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':args_json,'timestamp':utils.datetimeNow() }
            ell.log(app_id+':APP-CALL', log_entry  )


            # assign uid to each algorithm and save it
            # scott: alg_list copied from line 201 in PoolBasedTripletMDS.py
            alg_list = args_dict['alg_list']
            for algorithm in alg_list:
                alg_id = algorithm['alg_id']
                alg_uid = utils.getNewUID()
                algorithm['alg_uid'] = alg_uid

                db.set(app_id+':algorithms',alg_uid,'alg_id',alg_id)
                db.set(app_id+':algorithms',alg_uid,'alg_uid',alg_uid)
                db.set(app_id+':algorithms',alg_uid,'exp_uid',exp_uid)

            # Setting experiment parameters in the database
            # These parometers are global to all apps
            # instructions, algorithm_management_settings, etc
            db.set(app_id+':experiments', exp_uid, 'exp_uid', exp_uid)
            db.set(app_id+':experiments', exp_uid, 'app_id', app_id)
            db.set(app_id+':experiments', exp_uid, 'alg_list', alg_list)
            db.set(app_id+':experiments', exp_uid, 'algorithm_management_settings', args_dict['algorithm_management_settings'])
            db.set(app_id+':experiments', exp_uid, 'participant_to_algorithm_management', participant_to_algorithm_management)
            db.set(app_id+':experiments', exp_uid, 'instructions', args_json['instructions'])
            db.set(app_id+':experiments', exp_uid, 'debrief', args_json['debrief'])
            db.set(app_id+':experiments', exp_uid, 'num_tries', args_json['num_tries'])
            db.set(app_id+':experiments', exp_uid, 'git_hash', git_hash)

            # now create intitialize each algorithm
            for algorithm in alg_list:
                alg_id = algorithm['alg_id']
                alg_uid = algorithm['alg_uid']
                params = algorithm.get('params',None)

                # get sandboxed database for the specific app_id,alg_uid,exp_uid - closing off the rest of the database to the algorithm
                rc = ResourceClient(app_id,exp_uid,alg_uid,db)

                # get specific algorithm to make calls to
                alg = utils.get_app_alg(self.app_id,alg_id)

                # call initExp
                didSucceed,dt = utils.timeit(alg.initExp)(resource=rc,n=n,d=d,failure_probability=delta,params=params)

                log_entry = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'initExp','duration':dt,'timestamp':utils.datetimeNow() }
                ell.log( app_id+':ALG-DURATION', log_entry  )

            response_json = '{}'

            log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':response_json,'timestamp':utils.datetimeNow() }
            ell.log( app_id+':APP-RESPONSE', log_entry  )

            return response_json,True,''

        except Exception, err:
            return '{}', False, error



  def getQuery(self,exp_uid,args_json,db,ell):
      pass

  def processAnswer(self,exp_uid,args_json,db,ell):
      pass

  def predict(self,exp_uid,args_json,db,ell):
      pass

  def getStats(self,exp_uid,args_json,db,ell):
      pass


