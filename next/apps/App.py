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

# The directory where we store the .yaml files describing each app
APPS_DIR = ''

class App(AppPrototype):
    def __init__(self):
        self.app_id = 'PoolBasedTripletMDS'
        self.description = Verifier.description(APPS_DIR + self.app_id + '.yaml')

    def daemonProcess(self,exp_uid,args_json,db,ell):
        pass

    def initExp(self,exp_uid,args_json,db,ell):
        try:
            app_id = self.app_id

            args_json, success, messages = Verifier.verify(args_json):
            if not success:
                raise Exception("Failed to verify: {}".format(" \n".join(messages)))

            # Convert the args JSON to an args dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = "%s.initExp input args_json is in improper format" % self.app_id
                raise Exception(error)

            # remove any reminants of an experiment if it exists
            self.remove_experiment(app_id, exp_uid, db)

            # Database call that creates the experiment
            db.set('experiments_admin',exp_uid,'exp_uid',exp_uid)
            db.set('experiments_admin',exp_uid,'app_id',app_id)
            db.set('experiments_admin',exp_uid,'start_date',utils.datetime2str(utils.datetimeNow()))

            log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':args_json,'timestamp':utils.datetimeNow() }
            ell.log(app_id+':APP-CALL', log_entry  )

            # TODO: most of the for code below (lines 52 through 85) has been
            # written without testing.  Debug it and make sure it works.
            default_args = self.description['initExp']['values']['args']['values']
            implemented_algs = default_args['alg_list']['values']['alg_id']['values']

            algorithm_settings = args_dict['args']['algorithm_management_settings']['params']['proportions']

            # Check to make sure the proportions add up to 1
            # TODO: Check/move to verifier
            total_porportion = sum(alg['proportion'] for alg in algorithm_settings)
            if numpy.allclose(total_porportion, 1):
                raise Exception('The algorithm porportions must add up to 1 (the currently add up to {})'.format(total_porportion))

            # Perform checks on the algorithms then include those algs in the
            # experiment. It makes sure that a givn algorithm is implemented and
            # checks to make sure it's specified in
            # algorithm_management_settings
            alg_list = args_dict['alg_list']
            for algorithm in alg_list:
                alg_id = algorithm['alg_id']
                alg_uid = utils.getNewUID()
                algorithm['alg_uid'] = alg_uid

                # TODO: also verifier
                if algorithm not in implemented_algs:
                    raise Exception('An algorithm in alg_list ({}) is not implemented. It must be one of {}.'.format(alg_list, implemented_algs))

                # Verifier
                porportion_algorithms = [alg['alg_label'] for alg in algorithm_settings]
                if algorithm not in porportion_algorithms:
                    raise Exception('An algorithm in alg_list ({})is not in in algorithm_management_settings (in the apprpriate place'.format(algorithm))

                db.set(app_id+':algorithms',alg_uid,'alg_id',alg_id)
                db.set(app_id+':algorithms',alg_uid,'alg_uid',alg_uid)
                db.set(app_id+':algorithms',alg_uid,'exp_uid',exp_uid)

            # Setting experiment parameters in the database
            db.set(app_id+':experiments', exp_uid, 'exp_uid', exp_uid)
            db.set(app_id+':experiments', exp_uid, 'app_id', app_id)
            db.set(app_id+':experiments', exp_uid, 'alg_list', alg_list)
            db.set(app_id+':experiments', exp_uid, 'git_hash', git_hash)

            # Put the dictionary for the experiment in the database.
            # These keys are more general and apply to both apps
            for key in args_json.keys():
                db.set(app_id+':experiments', exp_uid, key, args_json[key])

            # These are the arguments specfic to this particular app
            for key in args_dict.keys():
                db.set(app_id+':experiments', exp_uid, key, args_dict[key])

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

  def remove_experiment(self, app_id, exp_uid, db):
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
