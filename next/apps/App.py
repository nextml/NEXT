"""
This file collects common code for every app. It is general across all apps and
makes a call to the specified app in the appropriate place.

Apps are specified with a YAML file with a specific structure. A given instance
of an app is verified before creation.
"""

# TODO: include docstrings (copy and paste from PoolBasedTripletsMDS.py)
import os
import sys
import numpy
import numpy.random
import json
import yaml
import traceback
import next.utils as utils
import next.apps.Verifier as Verifier
import next.constants
import next.apps.Butler as Butler

Butler = Butler.Butler
git_hash = next.constants.GIT_HASH


#TODO: App Exception logs
#TODO: move __import__ to importlib
class App(object):
    def __init__(self, app_id, exp_uid, db, ell):
        self.app_id = app_id
        self.exp_uid = exp_uid
        self.helper = Helper()
        self.myApp = __import__('next.apps.Apps.'+self.app_id, fromlist=[''])
        self.myApp = getattr(self.myApp, app_id)
        self.myApp = self.myApp(db)
        self.butler = Butler(self.app_id, self.exp_uid, self.myApp.TargetManager, db, ell)
        dir,_ = os.path.split(__file__)
        with open(os.path.join(dir, "Apps/{}/{}.yaml".format(app_id, app_id)),'r') as f:
            self.reference_dict = yaml.load(f)
        dashboard_string = 'next.apps.Apps.' + self.app_id + \
                           '.dashboard.Dashboard'
        dashboard_module = __import__(dashboard_string, fromlist=[''])
        self.dashboard = getattr(dashboard_module, app_id+'Dashboard')


    def initExp(self, exp_uid, args_json):
        try:
            self.helper.ensure_indices(self.app_id,self.butler.db, self.butler.ell)
            args_dict = self.helper.convert_json(args_json)
            args_dict = Verifier.verify(args_dict, self.reference_dict['initExp']['values'])
            args_dict['exp_uid'] = exp_uid # to get doc from db
            args_dict['start_date'] = utils.datetime2str(utils.datetimeNow())
            self.butler.admin.set(uid=exp_uid,value={'exp_uid': exp_uid, 'app_id':self.app_id, 'start_date':str(utils.datetimeNow())}) 
            args_dict,algs_args_dict = self.myApp.initExp(exp_uid, args_dict, self.butler)
            # Set doc in algorithms bucket. These objects are used by the algorithms to store data.
            for algorithm in args_dict['args']['alg_list']:
                algorithm['exp_uid'] = exp_uid
                self.butler.algorithms.set(uid=algorithm['alg_label'], value=algorithm)
            args_dict['git_hash'] = git_hash
            self.butler.experiment.set(value=args_dict)
            for algorithm in args_dict['args']['alg_list']:
                params = algorithm.get('params',None)
                butler = Butler(self.app_id, exp_uid, self.myApp.TargetManager, self.butler.db, self.butler.ell, algorithm['alg_label'], algorithm['alg_id'])
                alg = utils.get_app_alg(self.app_id, algorithm['alg_id'])

                # utils.debug_print("App.py:66, algs_args_dict = {}".format(algs_args_dict))
                # I got rid of a timeit function here; it wasn't handling the
                # argument unpacking correctly? --Scott, 2016-3-7
                # TODO: put dt back in and change log_entry to relfect that
                alg.initExp(butler,params=params, **algs_args_dict)
                if not True:
                    raise Exception('Algorithm {} failed to initialize.'.format(algorithm['alg_label']))

                log_entry = {'exp_uid':exp_uid, 'alg_label':algorithm['alg_label'], 'task':'initExp', 'duration':-1, 'timestamp':utils.datetimeNow()}
                self.butler.log('ALG-DURATION', log_entry)
            return '{}', True, ''
        except Exception, error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_error = str(traceback.format_exc())+'\n'+str(error)
            print "initExp Exception: " + full_error
            log_entry = { 'exp_uid':exp_uid,'task':'initExp','error':full_error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
            self.butler.ell.log( self.app_id+':APP-EXCEPTION', log_entry  )
            traceback.print_tb(exc_traceback)
            return '{}', False, str(error)


    def getQuery(self, exp_uid, args_json):
        try:
    	    args_dict = self.helper.convert_json(args_json)
            args_dict = Verifier.verify(args_dict, self.reference_dict['getQuery']['values'])
            experiment_dict = self.butler.experiment.get()
            alg_list = experiment_dict['args']['alg_list']
            participant_to_algorithm_management = experiment_dict['args']['participant_to_algorithm_management']
            algorithm_management_settings = experiment_dict['args']['algorithm_management_settings']
            # Create the participant dictionary in participants bucket if needed. Also pull out label and id for this algorithm
            participant_uid = args_dict['args'].get('participant_uid', args_dict['exp_uid'])
            # Check to see if the first participant has come by and if not, save to db
            participant_doc = self.butler.participants.get(uid=participant_uid)
            first_participant_query = participant_doc==None
            if first_participant_query:
                participant_doc = {}
            if first_participant_query:
                self.butler.participants.set(uid=participant_uid, value={'exp_uid':exp_uid, 'participant_uid':participant_uid})
            if (participant_uid == exp_uid) or (participant_to_algorithm_management == 'one_to_many') or (first_participant_query):
                if algorithm_management_settings['mode'] == 'fixed_proportions':
                    prop = [prop_item['proportion'] for prop_item in algorithm_management_settings['params']]
                    chosen_alg = numpy.random.choice(alg_list, p=prop)
                alg_id = chosen_alg['alg_id']
                alg_label = chosen_alg['alg_label']
                if  (first_participant_query) and (participant_to_algorithm_management=='one_to_one'):
                    self.butler.participants.set(uid=participant_uid, key='alg_id',value=alg_id)
                    self.butler.participants.set(uid=participant_uid, key='alg_label',value=alg_label)
            elif (participant_to_algorithm_management=='one_to_one'):
                alg_id = participant_doc['alg_id']
                alg_label = participant_doc['alg_label']
            # Deal with the issue of not giving a repeat query
            butler = Butler(self.app_id, exp_uid, self.myApp.TargetManager, self.butler.db, self.butler.ell, alg_label, alg_id)
            alg = utils.get_app_alg(self.app_id, alg_id)
            alg_response,dt = utils.timeit(alg.getQuery)(butler,participant_doc,**args_dict)
            query_doc = self.myApp.getQuery(exp_uid, experiment_dict, args_dict, alg_response, self.butler)
            query_uid = utils.getNewUID()
            query_doc.update({'participant_uid':participant_uid,
                              'alg_id':alg_id,
                              'exp_uid':exp_uid,
                              'alg_label':alg_label,
                              'timestamp_query_generated':str(utils.datetimeNow()),
                              'query_uid':query_uid})
            self.butler.queries.set(uid=query_uid, value=query_doc)
            log_entry_durations = {'exp_uid':exp_uid,'alg_label':alg_label,'task':'getQuery','duration':dt }
            log_entry_durations.update(butler.algorithms.getDurations())
            return json.dumps({'args':query_doc,'meta':{'log_entry_durations':log_entry_durations}}), True,''
        except Exception, error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_error = str(traceback.format_exc())+'\n'+str(error)
            print "getQuery Exception: " + full_error
            log_entry = { 'exp_uid':exp_uid,'task':'getQuery','error':full_error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
            self.butler.ell.log( self.app_id+':APP-EXCEPTION', log_entry  )
            traceback.print_tb(exc_traceback)
            return '{}', False, str(error)

    def processAnswer(self, exp_uid, args_json):
        try:
            args_dict = self.helper.convert_json(args_json)
            args_dict = Verifier.verify(args_dict, self.reference_dict['processAnswer']['values'])
            # Update timing info in query
            query = self.butler.queries.get(uid=args_dict['args']['query_uid'])
            delta_datetime = (utils.str2datetime(args_dict['args'].get('timestamp_answer_received',None)) -
                              utils.str2datetime(query['timestamp_query_generated']))
            round_trip_time = delta_datetime.seconds + delta_datetime.microseconds/1000000.
            response_time = float(args_dict['args'].get('response_time',0.))
            butler = Butler(self.app_id, exp_uid, self.myApp.TargetManager, self.butler.db, self.butler.ell, query['alg_label'], query['alg_id'])
            alg = utils.get_app_alg(self.app_id, query['alg_id'])
            query_update,algs_args_dict = self.myApp.processAnswer(exp_uid, query, args_dict, self.butler)
            query_update.update({'response_time':response_time,'network_delay':round_trip_time - response_time})
            self.butler.queries.set_many(uid=args_dict['args']['query_uid'],key_value_dict=query_update)
            # Push query back to algorithm
            alg_succeed, dt = utils.timeit(alg.processAnswer)(butler, **algs_args_dict)
            log_entry_durations = {'exp_uid':exp_uid, 'alg_label':query['alg_label'], 'task':'processAnswer','duration':dt }
            log_entry_durations.update(butler.algorithms.getDurations())
            if not alg_succeed:
                raise Exception('Algorithm {} failed to processAnswer.'.format(query['alg_label']))
            return json.dumps({'args': {}, 'meta': {'log_entry_durations':log_entry_durations}}), True, ''
        except Exception, error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_error = str(traceback.format_exc())+'\n'+str(error)
            print "processAnswer Exception: " + full_error
            log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','error':full_error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
            self.butler.ell.log( self.app_id+':APP-EXCEPTION', log_entry  )
    	    traceback.print_tb(exc_traceback)
    	    raise Exception(error)

    def getModel(self, exp_uid, args_json):
        try:
            args_dict = self.helper.convert_json(args_json)
            args_dict = Verifier.verify(args_dict, self.reference_dict['getModel']['values'])
            
            alg_label = args_dict['args']['alg_label']
            args = self.butler.experiment.get(key='args')
            for algorithm in args['alg_list']:
                if alg_label == algorithm['alg_label']:
                    alg_id = algorithm['alg_id']
            alg = utils.get_app_alg(self.app_id, alg_id)
            butler = Butler(self.app_id, exp_uid, self.myApp.TargetManager, self.butler.db, self.butler.ell, alg_label, alg_id)
            alg_response, dt = utils.timeit(alg.getModel)(butler)
            myapp_response = self.myApp.getModel(exp_uid, alg_response, args_dict, self.butler)
            myapp_response['exp_uid'] = exp_uid
            myapp_response['alg_label'] = alg_label
            # Log the response of the getModel in ALG-EVALUATION
            if args_dict['args']['logging']:
                alg_log_entry = {'exp_uid': exp_uid, 'alg_label':alg_label, 'task': 'getModel', 'timestamp': str(utils.datetimeNow())}
                alg_log_entry.update(myapp_response)
                self.butler.log('ALG-EVALUATION', alg_log_entry)
            log_entry_durations = { 'exp_uid':exp_uid,'alg_label':alg_label,'task':'getModel','duration':dt }
            log_entry_durations.update(butler.algorithms.getDurations())
            return json.dumps({'args': myapp_response,
                               'meta': {'log_entry_durations':log_entry_durations, 'timestamp': str(utils.datetimeNow())}}), True, ''
        except Exception, error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_error = str(traceback.format_exc())+'\n'+str(error)
            print "getModel Exception: " + full_error
            log_entry = { 'exp_uid':exp_uid,'task':'getModel','error':full_error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
            self.butler.ell.log( self.app_id+':APP-EXCEPTION', log_entry  )
            traceback.print_tb(exc_traceback)       
            return Exception(error)


class Helper(object):
    #TODO: This is never called?? Can we please remove this class?
    def remove_experiment(self, app_id, exp_uid, db, ell):
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

    def ensure_indices(self,app_id,db,ell):
        # add indexes (only adds them if they do not already exist)
        didSucceed,message = db.ensure_index('experiments_admin',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':experiments',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':queries',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':queries',{'participant_uid':1})
        didSucceed,message = db.ensure_index(app_id+':participants',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':participants',{'participant_uid':1})
        didSucceed,message = db.ensure_index(app_id+':algorithms',{'exp_uid':1})
        didSucceed,message = db.ensure_index(app_id+':algorithms',{'exp_uid':1,'alg_label':1})

        didSucceed,message = ell.ensure_index(app_id+':APP-EXCEPTION',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-DURATION',{'exp_uid':1,'alg_label':1,'task':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-EVALUATION',{'exp_uid':1})
        didSucceed,message = ell.ensure_index(app_id+':ALG-EVALUATION',{'exp_uid':1,'alg_label':1})

    def convert_json(self, args_json):
        #TODO: I'd like to see this in utils rather than here.
        # Convert the args JSON to an args dict
        try:
            return json.loads(args_json)
        except:
            error = "%s.initExp input args_json is in improper format" % self.app_id
            raise Exception(error)
