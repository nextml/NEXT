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

from next.resource_client.ResourceClient import ResourceClient
import next.utils as utils
import next.apps.Verifier as Verifier

import next.constants
git_hash = next.constants.GIT_HASH

class App(object):
    def __init__(self, app_id):
        self.app_id = app_id
        self.helper = Helper()
        #TODO: Switch to importlib
        # Import the app and call it self.myApp. For example, this line imports
        # the file in ./Apps/PoolBasedTripletMDS/PoolBasedTripletMDS.py
        self.myApp = __import__('next.apps.Apps.'+self.app_id, fromlist=[''])
        self.myApp = getattr(self.myApp, app_id)
        self.myApp = self.myApp()
        dir,_ = os.path.split(__file__)
        with open(os.path.join(dir, "Apps/{}/{}.yaml".format(app_id, app_id)),'r') as f:
            print "trying to open reference_dict"
            self.reference_dict = yaml.load(f)
        #TODO: Move to get stats
        dashboard_string = 'next.apps.Apps.' + self.app_id + \
                           '.dashboard.Dashboard'
        dashboard_module = __import__(dashboard_string, fromlist=[''])
        self.dashboard = getattr(dashboard_module, app_id+'Dashboard')
    ## Begin API function implementations

    def initExp(self, exp_uid, args_json, db, ell):
        try:
            app_id = self.app_id
            args_dict = self.helper.convert_json(args_json)
            try:
                args_dict, success, messages = Verifier.verify(args_dict, self.reference_dict['initExp']['values'])

                if not success:
                    print "Failed to verify:", messages, type(messages)
                    raise Exception("Failed to verify: {}".format(" \n".join(messages)))
            except Exception, error:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print "initExp Exception: {} {}".format(error, traceback.format_exc())
                traceback.print_tb(exc_traceback)
                raise Exception(error)
            
            args_dict['exp_uid'] = exp_uid # to get doc from db
            args_dict = self.myApp.initExp(exp_uid, args_dict, db, ell);
            print "verified args_dict", args_dict, type(args_dict)
            # remove any reminants of an experiment if it exists
            self.helper.remove_experiment(app_id, exp_uid, db, ell)

            # Set doc in experiment_admin bucket
            db.set_doc('experiments_admin', exp_uid, {'exp_uid': exp_uid, 'app_id':app_id, 'start_date': utils.datetime2str(utils.datetimeNow())})

            # Set doc in algorithms bucket. These objects are used by the algorithms to store data.
            for algorithm in args_dict['args']['alg_list']:
                algorithm['exp_uid'] = exp_uid 
                # This doc_uid is used by the ResourceClient
                db.set_doc(app_id+':algorithms', exp_uid+'_'+algorithm['alg_label'], algorithm)

            # Set doc in experiments bucket
            db.set_doc(app_id+':experiments', exp_uid, args_dict)
            db.set(app_id+':experiments', exp_uid, 'git_hash', git_hash)
            # now intitialize each algorithm
            for algorithm in args_dict['args']['alg_list']:
                params = algorithm.get('params',None)
                # get sandboxed database for the specific app_id, alg_uid, exp_uid - closing off the rest of the database to the algorithm
                rc = ResourceClient(app_id, exp_uid, algorithm['alg_label'], db)
                # get specific algorithm to make calls to
                alg = utils.get_app_alg(self.app_id, algorithm['alg_id'])
                # call initExp
                didSucceed, dt = utils.timeit(alg.initExp)(resource=rc,
                                                           params=params,
                                                           **args_dict['args'])
                log_entry = {'exp_uid':exp_uid,
                             'alg_id':algorithm['alg_id'],
                             'task':'initExp',
                             'duration':dt,
                             'timestamp':utils.datetimeNow()}

                ell.log(app_id+':ALG-DURATION', log_entry)
                print "logging algorithm", algorithm['alg_id']
            return '{}', True, ''
        except Exception, error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print "initExp Exception: {} {}".format(error, traceback.format_exc())
            traceback.print_tb(exc_traceback)
            return '{}', False, str(error)

		
    def getQuery(self, exp_uid, args_json, db, ell):
        try:
            app_id = self.app_id
	    args_dict = self.helper.convert_json(args_json)
	    print 'getQuery', args_dict
            try:
                args_dict, success, messages = Verifier.verify(args_dict, self.reference_dict['getQuery']['values'])
                if not success:
                    print '\n'*5 + 'App.py:getQuery verify error' + '\n'*2
                    print messages
                    raise Exception("Failed to verify: {}".format(" \n".join(messages)))
            except Exception, error:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		print "Exception! {} {}".format(error, traceback.format_exc())
		traceback.print_tb(exc_traceback)
		raise Exception(error)

            alg_list, _ ,_ = db.get(app_id+':experiments', exp_uid, 'args')
            alg_list = alg_list['alg_list']
            initExp_args_dict, didSucceed, message = db.get_doc(app_id + ':experiments', exp_uid)
                            # Create the participant dictionary in participants bucket if needed. Also pull out label and id for this algorithm
            participant_uid = args_dict['args'].get('participant_uid', args_dict['exp_uid'])
                # check to see if the first participant has come by and if not, save to db
            first_participant_query = not db.exists(app_id+':participants',participant_uid,'participant_uid')
            participant_to_algorithm_management = db.get(app_id+':experiments', exp_uid, 'args')[0]['participant_to_algorithm_management']
            if (participant_uid == exp_uid) or (participant_to_algorithm_management == 'one_to_many') or (first_participant_query):
                algorithm_management_settings = initExp_args_dict['args']['algorithm_management_settings']
                if algorithm_management_settings['mode'] == 'fixed_proportions':
                    prop = [prop_item['proportion'] for prop_item in algorithm_management_settings['params']]
                    chosen_alg = numpy.random.choice(alg_list, p=prop)
                else:
                    raise Exception('algorithm_management_mode : '+algorithm_management_settings['mode']+' not implemented')
                alg_id = chosen_alg['alg_id']
                alg_label = chosen_alg['alg_label']
                if  (first_participant_query) and (participant_to_algorithm_management=='one_to_one'):
		    db.set_doc(app_id+':participants',participant_uid,{'exp_uid':exp_uid,
								       'participant_uid':participant_uid,
                                                                       'alg_id':alg_id,
                                                                       'alg_label':alg_label})
            elif (participant_to_algorithm_management=='one_to_one'):
                # If here, then alg_uid should already be assigned in participant doc
                alg_id,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_id')
                alg_label,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_label')
            else:
                raise Exception('participant_to_algorithm_management : '+participant_to_algorithm_management+' not implemented')

            # TODO: Figure out a good way of handling this.
            # figure out which queries have already been asked
            # queries,didSucceed,message = db.get_docs_with_filter(app_id+':queries',{'participant_uid':participant_uid})
            # do_not_ask_list = []
            # for q in queries:
            #     for t in q.get('target_indices',[]):
            #         do_not_ask_list.append(t['index'])
            # do_not_ask_list = list(set(do_not_ask_list))

            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(app_id, exp_uid, alg_label, db)
            alg = utils.get_app_alg(self.app_id, alg_id)
            alg_response = utils.timeit(alg.getQuery)(resource=rc)
            query = self.myApp.getQuery(exp_uid, args_dict, alg_response, db, ell)

            # save query data to database
            query_doc = {}
            query_doc.update(query)
            query_uid = utils.getNewUID()
            query_doc.update({'participant_uid':participant_uid,
                              'alg_id':alg_id,
                              'exp_uid':exp_uid,
                              'alg_label':alg_label,
                              'timestamp_query_generated':str(utils.datetimeNow()),
                              'query_uid':query_uid})
            db.set_doc(app_id+':queries', query_uid, query_doc)
            print "aasdfafasfsdf", app_id
            return json.dumps(query_doc), True,''
        except Exception, error:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            #print "getQuery Exception: {} {}".format(error, traceback.format_exc())
            traceback.print_tb(exc_traceback)
            return '{}', False, str(error)
        #TODO: App exception logs
            # error = traceback.format_exc()
            # log_entry = { 'exp_uid':exp_uid,'task':'getQuery','error':error,'timestamp':utils.datetimeNow(),'args_json':args_json }
            # ell.log( app_id+':APP-EXCEPTION', log_entry  )
            # return '{}',False,error

    def processAnswer(self, exp_uid, args_json, db, ell):
        # modified PoolBasedTripletsMDS.py
        try:
            app_id = self.app_id
            args_dict = self.helper.convert_json(args_json)
            try:
                args_dict, success, messages = Verifier.verify(args_dict, self.reference_dict['processAnswer']['values'])
                if not success:
                    print '\n'*5 + 'App.py:processAnswer verify error' + '\n'*2
                    print messages
                    raise Exception("Failed to verify: {}".format(" \n".join(messages)))
            except Exception, error:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		print "Exception! {} {}".format(error, traceback.format_exc())
		traceback.print_tb(exc_traceback)
		raise Exception(error)

            # Update timing info in query
            query, didSucceed, message = db.get_doc(app_id + ':queries', args_dict['args']['query_uid'])
            timestamp_query_generated = utils.str2datetime(query['timestamp_query_generated'])
            timestamp_answer_received = utils.str2datetime(args_dict['args'].get('timestamp_answer_received',None))
            delta_datetime = timestamp_answer_received - timestamp_query_generated
            round_trip_time = delta_datetime.seconds + delta_datetime.microseconds/1000000.
            response_time = float(args_dict['args'].get('response_time',0.))
            db.set(app_id+':queries',args_dict['args']['query_uid'],'response_time',response_time)
            db.set(app_id+':queries',args_dict['args']['query_uid'],'network_delay',round_trip_time-response_time)
            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(app_id, exp_uid, query['alg_label'], db)
            alg = utils.get_app_alg(self.app_id, query['alg_id'])
            app_response = self.myApp.processAnswer(exp_uid, args_dict, db)

            # Update query with processAnswer edits
            print "app_response", app_response, type(app_response)
            for key in app_response['doc']:
                db.set(app_id+':queries', args_dict['args']['query_uid'], key, app_response['doc'][key])

            # Call algorithm with algorithm specific data
            didSucceed, dt = utils.timeit(alg.processAnswer)(resource=rc, **app_response['alg'])
            # TODO: Where does this timing actually get logged?
            log_entry_durations = { 'exp_uid':exp_uid,'alg_label':query['alg_label'],'task':'processAnswer','duration':dt }
            log_entry_durations.update( rc.getDurations() )
            args_out = {'args': {}, 'meta': {'log_entry_durations':log_entry_durations}}
            # TODO: There should be a flag here to return the widget html if needed
            return json.dumps(args_out), True, ""
        except Exception:
            error = traceback.format_exc()
            log_entry = {'exp_uid': exp_uid, 'task': 'processAnswer',
                         'error': error, 'timestamp': utils.datetimeNow()}
            ell.log(app_id+':APP-EXCEPTION', log_entry)
            return '{}', False, error

    #TODO: Rename to getModel
    def getModel(self, exp_uid, args_json, db, ell):
        try:
            app_id = self.app_id
            args_dict = self.helper.convert_json(args_json)            
            try:
                args_dict, success, messages = Verifier.verify(args_dict, self.reference_dict['getModel']['values'])
                if not success:
                    print '\n'*5 + 'App.py:getModel verify error' + '\n'*2
                    print messages
                    raise Exception("Failed to verify: {}".format(" \n".join(messages)))
            except Exception, error:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		print "Exception! {} {}".format(error, traceback.format_exc())
		traceback.print_tb(exc_traceback)
		raise Exception(error)

            alg_label = args_dict['args']['alg_label']
            
            # get specific algorithm to make calls to
            alg_list, didSucceed, message = db.get(app_id + ':experiments',exp_uid,'alg_list')
            for algorithm in alg_list:
                if alg_label == algorithm['alg_label']:
                    alg_id = algorithm['alg_id']
            alg = utils.get_app_alg(self.app_id, alg_id)
            
            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(self.app_id, exp_uid, alg_label, db)
            alg_response,dt = utils.timeit(alg.getModel)(rc)
            myapp_response, meta = self.myApp.getModel(exp_uid, alg_response, args_dict, rc, db)
            args_out = {'args': myapp_response,
                        'meta': {'log_entry_durations':{'exp_uid':exp_uid,
                                                        'alg_label':alg_label,
                                                        'task':'getModel',
                                                        'duration':dt}}}
            if args_dict['args']['logging']:
                log_entry = {'exp_uid': exp_uid, 'task': 'getModel', 'json': args_out, 'timestamp': str(utils.datetimeNow())}
                ell.log(app_id+':APP-RESPONSE', log_entry)
            return json.dumps(args_out), True, ''
        except Exception:
            error = traceback.format_exc()
            log_entry = {'exp_uid': exp_uid, 'task': 'getModel',
                         'error': str(error), 'timestamp': utils.datetimeNow()}

            didSucceed,message = ell.log(app_id+':APP-EXCEPTION', log_entry)
            return '{}', False, error

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

class Helper(object):

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

    def convert_json(self, args_json):
            # Convert the args JSON to an args dict
            try:
                return json.loads(args_json)
            except:
                error = "%s.initExp input args_json is in improper format" % self.app_id
                raise Exception(error)

