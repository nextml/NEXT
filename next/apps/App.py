"""
This file collects common code for every app. It is general across all apps and
makes a call to the specified app in the appropriate place.

Apps are specified with a YAML file with a specific structure. A given instance
of an app is verified before creation.

Author: Scott Sievert, stsievert@wisc.edu
Creation date: 2016-1-11
"""

# TODO: include docstrings (copy and paste from PoolBasedTripletsMDS.py)

import numpy
import numpy.random
import json
import yaml
import time
import traceback

from next.resource_client.ResourceClient import ResourceClient
import next.utils as utils
from next.apps.AppPrototype import AppPrototype
import next.apps.Verifier as Verifier

import next.constants
git_hash = next.constants.GIT_HASH

# keys common to all algorithms.
common_keys = ['alg_list', 'algorithm_management_settings', 'debrief',
               'instructions', 'participant_to_algorithm_management']

class App(AppPrototype):
    def __init__(self, app_id):
        self.app_id = app_id

        #TODO: Switch to importlib
        # Import the app and call it self.myApp. For example, this line imports
        # the file in ./Apps/PoolBasedTripletMDS/PoolBasedTripletMDS.py
        self.myApp = __import__('next.apps.Apps.'+self.app_id, fromlist=[''])

        # Import the app's dashboard. The implementation of this dashboard
        # (which computes the results) is found in
        # Apps/myApp/dashboard/Dashboard.py and is named myAppDashboard (e.g.,
        # PoolBasedTripletsMDSDashboard)
        dashboard_string = 'next.apps.Apps.' + self.app_id + \
                           '.dashboard.Dashboard.' + self.app_id + 'Dashboard'
        self.dashboard = __import__(dashboard_string, fromlist=[''])

    def daemonProcess(self, exp_uid, args_json, db, ell):
        try:
            app_id = self.app_id

            log_entry = {'exp_uid': exp_uid, 'task': 'daemonProcess',
                         'json': args_json, 'timestamp': utils.datetimeNow()}
            ell.log(app_id+':APP-CALL', log_entry)

            # convert args_json to args_dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = '%s.daemonProcess input args_json is in improper format' % self.app_id
                return '{}', False, error

            # check for the fields that are necessary in args or error occurs
            key_check = Verifier.necessary_fields_present(args_dict, self.myApp.necessary_fields['daemonProcess'])
            if keys_check[0]:
                raise(key_check[1])

            alg_daemon_args = args_dict['daemon_args']
            alg_uid = args_dict['alg_uid']
            alg_id, didSucceed, message = db.get(app_id+':algorithms', alg_uid, 'alg_id')

            # get sandboxed database for the specific app_id,alg_id,exp_uid -
            # closing off the rest of the database to the algorithm
            rc = ResourceClient(app_id, exp_uid, alg_uid, db)

            # get specific algorithm to make calls to
            alg = utils.get_app_alg(self.app_id, alg_id)

            # TODO: these keyword args are not general and don't apply to all
            # apps... but do the necessary_fields change for daemonProcess
            # change from app to app?
            # Scott Sievert, 2016-1-14
            didSucceed, dt = utils.timeit(alg.daemonProcess)(resource=rc, daemon_args_dict=alg_daemon_args)

            log_entry = {'exp_uid': exp_uid, 'alg_uid': alg_uid,
                         'task': 'daemonProcess', 'duration': dt,
                         'timestamp': utils.datetimeNow()}

            log_entry_durations = {'exp_uid': exp_uid, 'alg_uid': alg_uid,
                                   'task': 'daemonProcess', 'duration': dt}
            log_entry_durations.update(rc.getDurations())
            meta = {'log_entry_durations': log_entry_durations}

            daemon_message = {}
            args_out = {'args': daemon_message, 'meta': meta}
            response_json = json.dumps(args_out)

            log_entry = {'exp_uid': exp_uid, 'task': 'daemonProcess',
                         'json': response_json,
                         'timestamp': utils.datetimeNow()}
            ell.log(app_id + ':APP-RESPONSE', log_entry)

            return response_json, True, ''

        # TODO: PEP8 tool says there's invalid syntax here... fix that!
        except Exception, err:
            error = traceback.format_exc()
            log_entry = {'exp_uid': exp_uid, 'task': 'daemonProcess',
                         'error': error, 'timestamp': utils.datetimeNow()}
            ell.log(app_id+':APP-EXCEPTION', log_entry)
            return '{}', False, error

        
    def initExp(self, exp_uid, args_json, db, ell):
        try:
            app_id = self.app_id
            with open('Apps/{}/{}.yaml'.format(app_id),'r') as f:
                reference_dict = yaml.load(f)['initExp']
            args_dict = self.helper.convert_json(args_json)
            args_dict, success, messages = Verifier.verify(args_dict, )
            if not success:
                raise Exception("Failed to verify: {}".format(" \n".join(messages)))
            args_dict = self.myApp.initExp(exp_uid, args_dict, db, ell);
            
            # remove any reminants of an experiment if it exists
            self.remove_experiment(app_id, exp_uid, db)

            # Database call that creates the experiment
            db.set('experiments_admin',exp_uid,'exp_uid',exp_uid)
            db.set('experiments_admin',exp_uid,'app_id',app_id)
            db.set('experiments_admin',exp_uid,'start_date',utils.datetime2str(utils.datetimeNow()))

            log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':args_json,'timestamp':utils.datetimeNow() }
            ell.log(app_id+':APP-CALL', log_entry  )

            alg_list = args_dict['alg_list']
            for algorithm in alg_list:
                alg_id = algorithm['alg_id']
                alg_uid = utils.getNewUID()
                algorithm['alg_uid'] = alg_uid

                db.set(app_id+':algorithms', alg_uid, 'alg_id', alg_id)
                db.set(app_id+':algorithms', alg_uid, 'alg_uid', alg_uid)
                db.set(app_id+':algorithms', alg_uid, 'exp_uid', exp_uid)

            # Setting experiment parameters in the database
            db.set(app_id+':experiments', exp_uid, 'exp_uid', exp_uid)
            db.set(app_id+':experiments', exp_uid, 'app_id', app_id)
            db.set(app_id+':experiments', exp_uid, 'alg_list', alg_list)
            db.set(app_id+':experiments', exp_uid, 'git_hash', git_hash)

            # These are the arguments specfic to this particular app
            for key in args_dict.keys():
                db.set(app_id+':experiments', exp_uid, key, args_dict[key])

            # now intitialize each algorithm
            for algorithm in alg_list:
                params = algorithm.get('params',None)
                # get sandboxed database for the specific app_id, alg_uid,
                # exp_uid - closing off the rest of the database to the algorithm
                rc = ResourceClient(app_id, exp_uid, algorithm[alg_uid], db)
                # get specific algorithm to make calls to
                alg = utils.get_app_alg(self.app_id, algorithm[alg_id])
                # call initExp
                didSucceed, dt = utils.timeit(alg.initExp)(resource=rc,
                                                           params=params,
                                                           **alg_args)
                log_entry = {'exp_uid':exp_uid,
                             'alg_uid':alg_uid,
                             'task':'initExp',
                             'duration':dt,
                             'timestamp':utils.datetimeNow()}
                ell.log(app_id+':ALG-DURATION', log_entry)

            log_entry = { 'exp_uid':exp_uid, 'task':'initExp', 'json':response_json,
                          'timestamp':utils.datetimeNow()}
            ell.log( app_id+':APP-RESPONSE', log_entry)
            return {}, True, ''
        except Exception, err:
            return {}, False, error

    def getQuery(self, exp_uid, args_json, db, ell):
        try:
            app_id = self.app_id
            with open('Apps/{}/{}.yaml'.format(app_id),'r') as f:
                reference_dict = yaml.load(f)['getQuery']
            args_dict = self.helper.convert_json(args_json)
            args_dict, success, messages = Verifier.verify(args_dict, reference_dict)
            if not success:
                raise Exception("Failed to verify: {}".format(" \n".join(messages)))

            alg_list, _, _ = db.get(app_id+':experiments',exp_uid,'alg_list')
            alg_label_to_alg_id = {}
            alg_label_to_alg_uid = {}
            for algorithm in alg_list:
                alg_label_to_alg_id[algorithm['alg_label']] = algorithm['alg_id']
                alg_label_to_alg_uid[algorithm['alg_label']] = algorithm['alg_uid']

            response = db.get(app_id + ':experiments', exp_uid, 'algorithm_management_settings')
            algorithm_management_settings, didSucceed, message = response

            if 'participant_uid' in args_dict:
                participant_uid = args_dict['participant_uid']
            else:
                participant_uid = exp_uid

            # check to see if the first partipant has come by and if not, save to db
            participant_doc_exists, didSucceed, message = db.exists(app_id+':participants',participant_uid,'participant_uid')
            first_participant_query = not participant_doc_exists
            if first_participant_query:
                db.set(app_id+':participants', participant_uid, 'participant_uid', participant_uid)
                db.set(app_id+':participants', participant_uid, 'exp_uid', exp_uid)

            participant_to_algorithm_management,didSucceed,message = db.get(app_id+':experiments', exp_uid, 'participant_to_algorithm_management')
            # the real decisions in choosing a query (partipant_to_alg settings looked at, etc)
            if (participant_uid==exp_uid) or \
               (participant_to_algorithm_management=='one_to_many') or \
               (first_participant_query):

                if algorithm_management_settings['mode']=='fixed_proportions':
                    proportions_list = algorithm_management_settings['params']['proportions']
                    prop = [ prop_item['proportion'] for prop_item in proportions_list ]
                    prop_item = numpy.random.choice(alg_list,p=prop)
                else:
                    raise Exception('algorithm_management_mode : '+algorithm_management_settings['mode']+' not implemented')

                alg_id = alg_label_to_alg_id[ prop_item['alg_label'] ]
                alg_uid = alg_label_to_alg_uid[ prop_item['alg_label'] ]
                alg_label = prop_item['alg_label']

                if  (first_participant_query) and \
                        (participant_to_algorithm_management=='one_to_one'):
                    db.set(app_id+':participants',participant_uid,'alg_id',alg_id)
                    db.set(app_id+':participants',participant_uid,'alg_uid',alg_uid)

            elif (participant_to_algorithm_management=='one_to_one'):
                # If here, then alg_uid should already be assigned in participant doc
                alg_id,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_id')
                alg_uid,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_uid')
            else:
                raise Exception('participant_to_algorithm_management : '+participant_to_algorithm_management+' not implemented')

            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(app_id, exp_uid, alg_uid, db)

            # get specific algorithm to make calls to
            alg = utils.get_app_alg(self.app_id, alg_id)

            # call getQuery on the algorithm
            alg_response = utils.timeit(alg.getQuery)(resource=rc)

            # call getQuery on myApp
            app_response = self.myApp.getQuery(exp_uid, args_dict, alg_response, db, ell)
            query = app_response['query']
            timestamp = app_response['timestamp']
            query_uid = utils.getNewUID()
            # save query data to database
            query_doc = {}
            query_doc.update(query)
            query_doc.update({'participant_uid':participant_uid,
                              'alg_uid':alg_uid, 'exp_uid':exp_uid,
                              'alg_label':alg_label,
                              'timestamp_query_generated':timestamp})

            db.set_doc(app_id+':queries', query_uid, query_doc)

            args_out = {'args':query,'meta':meta}
            response_json = json.dumps(args_out)

            log_entry = { 'exp_uid':exp_uid,'task':'getQuery','json':response_json,'timestamp':utils.datetimeNow() }
            ell.log( app_id+':APP-RESPONSE', log_entry  )

            return response_json,True,''

        except Exception, err:
            error = traceback.format_exc()
            log_entry = { 'exp_uid':exp_uid,'task':'getQuery','error':error,'timestamp':utils.datetimeNow(),'args_json':args_json }
            ell.log( app_id+':APP-EXCEPTION', log_entry  )
            return '{}',False,error

        
    def processAnswer(self, exp_uid, args_json, db, ell):
        # modified PoolBasedTripletsMDS.py
        try:
            app_id = self.app_id

            log_entry = {'exp_uid': exp_uid, 'task': 'processAnswer',
                         'json': args_json, 'timestamp': utils.datetimeNow()}
            ell.log(app_id+':APP-CALL', log_entry)

            # convert args_json to args_dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = "%s.processAnswer input args_json is in improper format" % self.app_id
                raise Exception(error)

            # check for the fields that must be contained in args or error
            # occurs
            key_check = Verifier.necessary_fields_present(args_dict,
                                  self.myApp.necessary_fields['processAnswer'])
            if keys_check[0]:
                raise(key_check[1])

            # get list of algorithms associated with project
            alg_list, didSucceed, message = db.get(app_id + ':experiments',
                                                   exp_uid, 'alg_list')

            # get alg_id
            query_uid = args_dict['query_uid']
            alg_uid, didSucceed, message = db.get(app_id + ':queries',
                                                  query_uid, 'alg_uid')
            if not didSucceed:
                raise Exception("Failed to retrieve query with query_uid=" + query_uid)

            for algorithm in alg_list:
                if alg_uid == algorithm['alg_uid']:
                    alg_id = algorithm['alg_id']
                    alg_label = algorithm['alg_label']
                    test_alg_label = algorithm['test_alg_label']
                    response = db.increment(app_id + ':experiments', exp_uid,
                                            'num_reported_answers_for_' + alg_uid)
                    num_reported_answers, didSucceed, message = response

            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(app_id, exp_uid, alg_uid,db)

            # get specific algorithm to make calls to
            alg = utils.get_app_alg(self.app_id, alg_id)

            app_response, meta = self.myApp.processAnswer()
            # call processAnswer in the algorithm.
            didSucceed, dt = utils.timeit(alg.processAnswer)(resource=rc,
                                                            **app_response)

            response_args_dict = {}
            args_out = {'args': response_args_dict, 'meta': meta}
            response_json = json.dumps(args_out)

            log_entry = {'exp_uid': exp_uid, 'task': 'processAnswer',
                          'json': response_json,
                          'timestamp': utils.datetimeNow()}
            ell.log(app_id + ':APP-RESPONSE', log_entry)

            return response_json, True, ""

        except Exception, err:
            error = traceback.format_exc()
            log_entry = {'exp_uid': exp_uid, 'task': 'processAnswer',
                         'error': error, 'timestamp': utils.datetimeNow()}
            ell.log(app_id+':APP-EXCEPTION', log_entry)
            return '{}', False, error

    # def predict(self, exp_uid, args_json, db,ell):
    #     try:
    #         app_id = self.app_id

    #         log_entry = {'exp_uid': exp_uid,  'task': 'predict',
    #                      'json': args_json, 'timestamp': utils.datetimeNow()}
    #         ell.log(app_id+':APP-CALL', log_entry)

    #         # convert args_json to args_dict
    #         try:
    #             args_dict = json.loads(args_json)
    #         except:
    #             error = "%s.predict input args_json is in improper format" % self.app_id
    #             raise Exception(error)

    #         # check for the fields that must be contained in args or error occurs
    #         key_check = Verifier.necessary_fields_present(args_dict,
    #                                     self.myApp.necessary_fields['predict'])
    #         if keys_check[0]:
    #             raise(key_check[1])

    #         predict_id = args_dict['predict_id']
    #         params = args_dict['params']
    #         alg_label = params['alg_label']

    #         # get list of algorithms associated with project
    #         alg_list, didSucceed, message = db.get(app_id + ':experiments',
    #                                                exp_uid, 'alg_list')

    #         # get alg_id
    #         for algorithm in alg_list:
    #             if alg_label == algorithm['alg_label']:
    #                 alg_id = algorithm['alg_id']
    #                 alg_uid = algorithm['alg_uid']

    #         response_args_dict, meta = self.myApp.predict(exp_uid, alg_id,
    #                                                       predict_id, db)

    #         args_out = {'args': response_args_dict, 'meta': meta}
    #         predict_json = json.dumps(args_out)

    #         log_entry = {'exp_uid': exp_uid, 'task': 'predict',
    #                      'json': predict_json, 'timestamp': utils.datetimeNow()}

    #         ell.log(app_id+':APP-RESPONSE', log_entry)
    #         return predict_json, True, ''

    #     except Exception, err:
    #         error = traceback.format_exc()
    #         log_entry = {'exp_uid': exp_uid, 'task': 'predict',
    #                      'error': str(error), 'timestamp': utils.datetimeNow()}

    #         didSucceed,message = ell.log(app_id+':APP-EXCEPTION', log_entry)
    #         return '{}', False, error

    # def getStats(self, exp_uid, args_json, db, ell):
    #     try:
    #         app_id = self.app_id

    #         log_entry = {'exp_uid': exp_uid, 'task': 'getStats',
    #                      'json': args_json, 'timestamp': utils.datetimeNow()}
    #         ell.log(app_id+':APP-CALL', log_entry)

    #         # convert args_json to args_dict
    #         try:
    #             args_dict = json.loads(args_json)
    #         except:
    #             error = "%s.getStats input args_json is in improper format" % self.app_id
    #             return '{}', False, error

    #         key_check = Verifier.necessary_fields_present(args_dict,
    #                                         self.myApp.necessary_fields['getStats'])
    #         if keys_check[0]:
    #             raise(key_check[1])

    #         stat_id = args_dict['stat_id']
    #         params = args_dict['params']

    #         dashboard = self.dashboard

    #         stats = self.myApp.getStats(stat_id, params, dashboard)
    #         response_json = json.dumps(stats)

    #         log_entry = {'exp_uid': exp_uid, 'task': 'getStats',
    #                      'json': response_json, 'timestamp': utils.datetimeNow()}
    #         ell.log(app_id+':APP-RESPONSE', log_entry)

    #         return response_json, True, ''

    #     except Exception, err:
    #         error = traceback.format_exc()
    #         log_entry = {'exp_uid': exp_uid, 'task': 'getStats', 'error': error,
    #                      'timestamp': utils.datetimeNow(), 'args_json': args_json}
    #         ell.log(app_id + ':APP-EXCEPTION', log_entry)
    #         return '{}', False, error



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

    def create_experiment(self, app_uid, exp_id, db):
        # Database call that creates the experiment
        db.set('experiments_admin',exp_uid,'exp_uid',exp_uid)
        db.set('experiments_admin',exp_uid,'app_id',app_id)
        db.set('experiments_admin',exp_uid,'start_date',utils.datetime2str(utils.datetimeNow()))

        log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':args_json,'timestamp':utils.datetimeNow() }
        ell.log(app_id+':APP-CALL', log_entry  )

    def convert_json(args_json):
            # Convert the args JSON to an args dict
            try:
                return json.loads(args_json)
            except:
                error = "%s.initExp input args_json is in improper format" % self.app_id
                raise Exception(error)

    def associated_algs(self, db):

        return alg_list
