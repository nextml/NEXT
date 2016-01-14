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

class App(AppPrototype):
    def __init__(self):
        self.app_id = 'PoolBasedTripletMDS'
        self.myApp = __import__('next.apps.Apps.'+self.app_id, fromlist=[''])

        dashboard_string = 'next.apps.Apps.' + self.app_id + '.dashboard.Dashboard.'
                                + self.app_id + 'Dashboard'
        self.dashboard = __import__(dashboard_string, fromlist=[''])

        self.yaml_descriptor = 'Apps/' + self.app_id
        self.description = Verifier.description(self.yaml_descriptor)

    def associated_algs(self, db):
        alg_list, _, _ = db.get(app_id+':experiments',exp_uid,'alg_list')
        return alg_list

    def daemonProcess(self,exp_uid,args_json,db,ell):
        pass

    def processAnswer(self,exp_uid,args_json,db,ell):
        # modified PoolBasedTripletsMDS.py
        try:
            app_id = self.app_id

            log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','json':args_json,'timestamp':utils.datetimeNow() }
            ell.log( app_id+':APP-CALL', log_entry  )

            # convert args_json to args_dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = "%s.processAnswer input args_json is in improper format" % self.app_id
                raise Exception(error)

            # check for the fields that must be contained in args or error occurs
            necessary_fields = ['index_winner','query_uid']
            for field in necessary_fields:
                try:
                    args_dict[field]
                except KeyError:
                    error = "%s.processAnswer input arguments missing field: %s" % (self.app_id,str(field))
                    raise Exception(error)

            # get list of algorithms associated with project
            alg_list,didSucceed,message = db.get(app_id+':experiments',exp_uid,'alg_list')

            # get alg_id
            query_uid = args_dict['query_uid']
            alg_uid,didSucceed,message = db.get(app_id+':queries',query_uid,'alg_uid')
            if not didSucceed:
                raise Exception("Failed to retrieve query with query_uid="+query_uid)

            for algorithm in alg_list:
                if alg_uid == algorithm['alg_uid']:
                    alg_id = algorithm['alg_id']
                    alg_label = algorithm['alg_label']
                    test_alg_label = algorithm['test_alg_label']
                    num_reported_answers,didSucceed,message = db.increment(app_id+':experiments',exp_uid,'num_reported_answers_for_'+alg_uid)

            # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
            rc = ResourceClient(app_id,exp_uid,alg_uid,db)

            # get specific algorithm to make calls to
            alg = utils.get_app_alg(self.app_id,alg_id)

            app_response, meta = self.myApp.processAnswer()
            # call processAnswer in the algorithm.
            didSucceed, dt = utils.timeit(alg.processAnswer)(resource=rc,
                                                            **app_response)

            response_args_dict = {}
            args_out = {'args':response_args_dict,'meta':meta}
            response_json = json.dumps(args_out)

            log_entry = { 'exp_uid':exp_uid, 'task':'processAnswer',
                          'json':response_json, 'timestamp':utils.datetimeNow()}
            ell.log( app_id+':APP-RESPONSE', log_entry  )

            return response_json,True,""

        except Exception, err:
            error = traceback.format_exc()
            log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','error':error,'timestamp':utils.datetimeNow() }
            ell.log( app_id+':APP-EXCEPTION', log_entry  )
            return '{}', False, error

    def predict(self, exp_uid, args_json, db,ell):
        try:
            app_id = self.app_id

            log_entry = { 'exp_uid':exp_uid, 'task':'predict', 'json':args_json,
                          'timestamp':utils.datetimeNow()}

            ell.log( app_id+':APP-CALL', log_entry  )

            # convert args_json to args_dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = "%s.predict input args_json is in improper format" % self.app_id
                raise Exception(error)

            # check for the fields that must be contained in args or error occurs
            necessary_fields = ['predict_id', 'params']

            # TODO: (low priority) rework this into set/subset
            # something like set(args_dict).issubset(necessary_fields)
            #if not set(args_dict).issubset(necessary_fields):
                #error = "%s.predict input arguments missing field: %s" % (self.app_id, set(necessary_fields - args_dict))
                #raise Exception(error)

            for field in necessary_fields:
                try:
                    args_dict[field]
                except KeyError:
                    error = "%s.predict input arguments missing field: %s" % (self.app_id, str(field))
                    raise Exception(error)

            predict_id = args_dict['predict_id']
            params = args_dict['params']
            alg_label = params['alg_label']

            # get list of algorithms associated with project
            alg_list,didSucceed,message = db.get(app_id+':experiments',exp_uid,'alg_list')

            # get alg_id
            for algorithm in alg_list:
                if alg_label == algorithm['alg_label']:
                    alg_id = algorithm['alg_id']
                    alg_uid = algorithm['alg_uid']

            response_args_dict, meta = self.myApp.predict(exp_uid, alg_id,
                                                          predict_id, db)

            args_out = {'args':response_args_dict, 'meta':meta}
            predict_json = json.dumps(args_out)

            log_entry = { 'exp_uid':exp_uid, 'task':'predict',
                          'json':predict_json, 'timestamp':utils.datetimeNow()}

            ell.log( app_id+':APP-RESPONSE', log_entry  )

            return predict_json, True, ''

        except Exception, err:
            error = traceback.format_exc()
            log_entry = { 'exp_uid':exp_uid, 'task':'predict',
                          'error':str(error), 'timestamp':utils.datetimeNow()}

            didSucceed,message = ell.log( app_id+':APP-EXCEPTION', log_entry  )
            return '{}',False,error

    def getStats(self,exp_uid,args_json,db,ell):

        try:
            app_id = self.app_id

            log_entry = { 'exp_uid':exp_uid,'task':'getStats','json':args_json,'timestamp':utils.datetimeNow() }
            ell.log( app_id+':APP-CALL', log_entry  )

            # convert args_json to args_dict
            try:
                args_dict = json.loads(args_json)
            except:
                error = "%s.getStats input args_json is in improper format" % self.app_id
                return '{}',False,error

            # check for the fields that must be contained in args or error occurs
            # TODO: (low priority): use set and subset
            # TODO: make a helper function for this
            necessary_fields = ['stat_id','params']
            for field in necessary_fields:
                try:
                    args_dict[field]
                except KeyError:
                    error = "%s.getStats input arguments missing field: %s" % (self.app_id,str(field))
                    return '{}',False,error

            stat_id = args_dict['stat_id']
            params = args_dict['params']

            dashboard = self.dashboard

            stats = self.myApp.getStats(stat_id, params, dashboard)
            response_json = json.dumps(stats)

            log_entry = { 'exp_uid':exp_uid, 'task':'getStats',
                          'json':response_json, 'timestamp':utils.datetimeNow()}
            ell.log( app_id+':APP-RESPONSE', log_entry  )

            return response_json, True, ''

        except Exception, err:
            error = traceback.format_exc()
            log_entry = { 'exp_uid':exp_uid, 'task':'getStats', 'error':error,
                          'timestamp':utils.datetimeNow(),'args_json':args_json }
            ell.log( app_id+':APP-EXCEPTION', log_entry  )
            return '{}', False, error


    def getQuery(self,exp_uid,args_json,db,ell):
        try:
            app_id = self.app_id

            args_json, success, messages = Verifier.verify(args_json):
            if not success:
                raise Exception("Failed to verify: {}".format(" \n".join(messages)))

            args_dict = self.convert_json(args_json)
            alg_list = self.associated_algs(db)

            # TODO: wrap all this choose_alg to a function. This function will
            # look at all the if statements
            alg_label_to_alg_id = {}
            alg_label_to_alg_uid = {}
            for algorithm in alg_list:
                alg_label_to_alg_id[ algorithm['alg_label'] ] = algorithm['alg_id']
                alg_label_to_alg_uid[ algorithm['alg_label'] ] = algorithm['alg_uid']

            algorithm_management_settings,didSucceed,message = db.get(app_id+':experiments',exp_uid,'algorithm_management_settings')

            participant_uid = args_dict['participant_uid']

            # check to see if the first partipant has come by
            participant_doc_exists,didSucceed,message = db.exists(app_id+':participants',participant_uid,'participant_uid')
            first_participant_query = not participant_doc_exists
            if first_participant_query:
                db.set(app_id+':participants',participant_uid,'participant_uid',participant_uid)
                db.set(app_id+':participants',participant_uid,'exp_uid',exp_uid)

            participant_to_algorithm_management,didSucceed,message = db.get(app_id+':experiments',exp_uid,'participant_to_algorithm_management')

            # the real decisions in choosing a query (partipant_to_alg settings
            # looked at, etc)
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
            # TODO: test! I haven't the three big lines below, not even the most
            # basic tests
            app_response = self.myApp.getQuery(exp_uid, args_uid, alg_response)
            query, query_uid = app_response['query'], app_response['query_uid']
            timestamp = app_response['timestamp']

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

    def initExp(self,exp_uid,args_json,db,ell):
        try:
            app_id = self.app_id

            args_json, success, messages = Verifier.verify(args_json):
            if not success:
                raise Exception("Failed to verify: {}".format(" \n".join(messages)))

            args_dict = self.convert_json(args_json)

            # remove any reminants of an experiment if it exists
            self.remove_experiment(app_id, exp_uid, db)
            self.create_experiment(app_id exp_uid, db)

            # Perform checks on the algorithms then include those algs in the
            # experiment. It makes sure that a givn algorithm is implemented and
            # checks to make sure it's specified in
            # algorithm_management_settings
            # DEBUG/TODO: args_dict may need other keys (I'm thinking
            # args_dict['initExp']['args']['alg_list']
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

            # Put the dictionary for the experiment in the database.
            # These keys are more general and apply to both apps
            for key in args_json.keys():
                db.set(app_id+':experiments', exp_uid, key, args_json[key])

            # These are the arguments specfic to this particular app
            for key in args_dict.keys():
                db.set(app_id+':experiments', exp_uid, key, args_dict[key])

            # now intitialize each algorithm
            for algorithm in alg_list:
                alg_id = algorithm['alg_id']
                alg_uid = algorithm['alg_uid']
                params = algorithm.get('params',None)

                # get sandboxed database for the specific app_id,alg_uid,exp_uid - closing off the rest of the database to the algorithm
                rc = ResourceClient(app_id, exp_uid, alg_uid, db)

                # get specific algorithm to make calls to
                alg = utils.get_app_alg(self.app_id, alg_id)

                # TODO: make alg.iniExp accept more **kwargs for future proofing
                args = args_dict['initExp']['args']
                common_kwargs = ['alg_list', 'algorithm_management_settings', 'debrief',
                            'instructions', 'participant_to_algorithm_management']

                alg_args = {key: args[key] for key in args.keys()
                                        if key not in common_kwargs}

                # call initExp
                didSucceed, dt = utils.timeit(alg.initExp)(resource=rc,
                                              params=params, **alg_args)

                log_entry = { 'exp_uid':exp_uid, 'alg_uid':alg_uid, 'task':'initExp',
                              'duration':dt, 'timestamp':utils.datetimeNow() }
                ell.log( app_id+':ALG-DURATION', log_entry  )

            response_json = '{}'

            log_entry = { 'exp_uid':exp_uid, 'task':'initExp', 'json':response_json,
                          'timestamp':utils.datetimeNow()}
            ell.log( app_id+':APP-RESPONSE', log_entry  )

            return response_json,True,''

        except Exception, err:
            return '{}', False, error

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

