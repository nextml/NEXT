"""
DuelingBanditsPureExploration app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/11/2015

######################################
DuelingBanditsPureExploration

This module manages the execution of different algorithms implemented to solve the 
problem described in DuelingBanditsPureExplorationPrototype.py. See this file for
more info.
"""

import numpy
import numpy.random
import json
import time
import traceback

from next.resource_client.ResourceClient import ResourceClient
import next.utils as utils
from next.apps.AppPrototype import AppPrototype
from next.apps.DuelingBanditsPureExploration.dashboard.Dashboard import DuelingBanditsPureExplorationDashboard

class DuelingBanditsPureExploration(AppPrototype):

  def __init__(self): 
    self.app_id = 'DuelingBanditsPureExploration'

  def daemonProcess(self,exp_uid,args_json,db,ell):
    try:

      app_id = self.app_id

      log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','json':args_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-CALL', log_entry  )

      # convert args_json to args_dict
      try:
        args_dict = json.loads(args_json)
      except:
        error = "%s.daemonProcess input args_json is in improper format" % self.app_id
        return '{}',False,error

      # check for the fields that must be contained in args or error occurs
      necessary_fields = ['alg_uid','daemon_args']
      for field in necessary_fields:
        try:
          args_dict[field]
        except KeyError:
          error = "%s.daemonProcess input arguments missing field: %s" % (self.app_id,str(field)) 
          return '{}',False,error


      alg_daemon_args = args_dict['daemon_args']
      alg_uid = args_dict['alg_uid']
      alg_id,didSucceed,message = db.get(app_id+':algorithms',alg_uid,'alg_id')

      # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
      # rc = ResourceClient(app_id,exp_uid,alg_uid,db)
      rc = ResourceClient(app_id,exp_uid,alg_uid,db)

      # get specific algorithm to make calls to 
      alg = utils.get_app_alg(self.app_id,alg_id)

      didSucceed,dt = utils.timeit(alg.daemonProcess)(resource=rc,daemon_args_dict=alg_daemon_args)
      log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'daemonProcess','duration':dt } 
      log_entry_durations.update( rc.getDurations() )
      meta = {'log_entry_durations':log_entry_durations}

      daemon_message = {}
      args_out = {'args':daemon_message,'meta':meta}
      response_json = json.dumps(args_out)

      log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','json':response_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return response_json,True,''

    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','error':error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error

  def initExp(self,exp_uid,args_json,db,ell):
    """
    initialize the project and necessary experiments 

    Expected input (in json structure with string keys):
      (int) n: number of arms
      (float) failure_probability : confidence
      [optional] (list of dicts) alg_list : with fields (Defaults given by Info.get_app_default_alg_list)
            (string) alg_id : valid alg_id for this app_id
            (string) alg_label : unique identifier for algorithm (e.g. may have experiment with repeated alg_id's, but alg_labels must be unqiue, will also be used for plot legends
            [optional] (string) test_alg_label : must be one of the alg_label's in alg_list (Default is self)
      [optional] (dict) algorithm_management_settings : dictionary with fields (string) 'mode' and (dict) 'params'. mode in {'pure_exploration','explore_exploit','fixed_proportions'}. Default is 'fixed_proportions' and allocates uniform probability to each algorithm. If mode=fixed_proportions then params is a dictionary that contains the field 'proportions' which is a list of dictionaries with fields 'alg_label' and 'proportion' for all algorithms in alg_list. All proportions must be positive and sum to 1 over all algs in alg_list 
      [optional] (string) participant_to_algorithm_management : in {'one_to_one','one_to_many'}. Default is 'one_to_many'.
      [optional] (string) instructions
      [optional] (string) debrief
      [optional] (int) num_tries
    
    Expected output:
      if error:
        return (JSON) '{}', (bool) False, (str) error_str
      else:
        return (JSON) '{}', (bool) True,''

    Usage:
      initExp_response_json,didSucceed,message = app.initExp(db_API,exp_uid,initExp_args_json)

    Example input:
      initExp_args_json = {"participant_to_algorithm_management": "one_to_many", "alg_list": [{"alg_label": "BR_LilUCB", "alg_id": "BR_LilUCB", "params": {}}], "algorithm_management_settings": {"params": {"proportions": [{"alg_label": "BR_LilUCB", "proportion": 1.0}]}, "mode": "fixed_proportions"}, "failure_probability": 0.01, "n": 10}

    Example output:
      initExp_response_json = {}
    """

    try:
      app_id = self.app_id

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
      
      import next.constants
      git_hash = next.constants.GIT_HASH

      db.set('experiments_admin',exp_uid,'exp_uid',exp_uid)
      db.set('experiments_admin',exp_uid,'app_id',app_id)
      db.set('experiments_admin',exp_uid,'start_date',utils.datetime2str(utils.datetimeNow()))

      log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':args_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-CALL', log_entry  )

      # convert args_json to args_dict
      try:
        args_dict = json.loads(args_json)
      except:
        error = "%s.initExp input args_json is in improper format" % self.app_id
        return '{}',False,error

      # check for the fields that must be contained in args or error occurs
      necessary_fields = ['n','failure_probability']
      for field in necessary_fields:
        try:
          args_dict[field]

        except KeyError:
          error = "%s.initExp input arguments missing field: %s" % (self.app_id,str(field)) 
          return '{}',False,error

      n = args_dict['n']
      delta = args_dict['failure_probability']

      if 'alg_list' in args_dict:
        alg_list = args_dict['alg_list']
        supportedAlgs = utils.get_app_supported_algs(self.app_id)
        for algorithm in alg_list:
          if algorithm['alg_id'] not in supportedAlgs:
            error = "%s.initExp unsupported algorithm '%s' in alg_list" % (self.app_id,alg_id)
            return '{}',False,error
      else:
        alg_list = utils.get_app_default_alg_list(self.app_id)


      if 'instructions' not in args_dict:
        instructions = utils.get_app_default_instructions(app_id)
      else:
        instructions = args_dict['instructions']

      if 'debrief' not in args_dict:
        debrief = utils.get_app_default_instructions(app_id)
      else:
        debrief = args_dict['debrief']

      if 'num_tries' not in args_dict:
        num_tries = utils.get_app_default_num_tries(app_id)
      else:
        num_tries = args_dict['num_tries']

      if 'context_type' not in args_dict:
        context_type = 'none'
      else:
        context_type = args_dict['context_type']

      if 'context' not in args_dict:
        context = ''
      else:
        context = args_dict['context']

      # ALGORITHM_MANAGEMENT_MODE FORMATTING CHECK
      if 'algorithm_management_settings' not in args_dict:
        params = {}
        params['proportions'] = []
        for algorithm in alg_list:
          params['proportions'].append(  { 'alg_label': algorithm['alg_label'] , 'proportion':1./len(alg_list)}  )

        algorithm_management_settings = {}
        algorithm_management_settings['mode'] = 'fixed_proportions'
        algorithm_management_settings['params'] = params
      else:
        algorithm_management_settings = args_dict['algorithm_management_settings']

        try:
          mode = algorithm_management_settings['mode']
          params = algorithm_management_settings['params']
        except:
          error = "%s.initExp algorithm_management_settings must be a dictionary with fields 'mode' and 'params'" % (self.app_id)
          return '{}',False,error

        if mode == 'fixed_proportions':
          try:
            algorithm_proportions_list = params['proportions']
          except:
            error = "%s.initExp algorithm_management_settings['params'] must be a dictionary with field 'proportions'" % (self.app_id)
            return '{}',False,error

          # check if alg_labels are properly labeled
          for proportion_item in algorithm_proportions_list:
            proportion = proportion_item['proportion']
            target_alg_label = proportion_item['alg_label']
            target_alg_label_in_alg_list = False
            for algorithm in alg_list:
              if algorithm['alg_label']==target_alg_label:
                target_alg_label_in_alg_list = True
            if not target_alg_label_in_alg_list:
              error = "%s.initExp algorithm_management_settings['params']['proportions'] must be a list of dictionaries, each dictionary containing the fields 'alg_label' and 'proportion'. The 'alg_label' value must be one of the alg_labels in a provided alg_list and 'proportion' must be nonnegative and sum to 1 : '%s' not in provided alg_list" % (self.app_id,target_alg_label)
              return '{}',False,error

        elif mode == 'pure_exploration':
          error = "%s.initExp Sorry, '%s' is not yet supported." % (self.app_id,mode)
          return '{}',False,error
        elif mode == 'explore_exploit':
          error = "%s.initExp Sorry, '%s' is not yet supported." % (self.app_id,mode)
          return '{}',False,error
        else:
          error = "%s.initExp unsupported algorithm_management_mode: '%s'. Must be in {'pure_exploration','explore_exploit','fixed_proportions'}" % (self.app_id,algorithm_management_mode)
          return '{}',False,error

      # ALGORITHM_MANAGEMENT_MODE FORMATTING CHECK
      if 'participant_to_algorithm_management' not in args_dict:
        participant_to_algorithm_management = 'one_to_many'
      else:
        participant_to_algorithm_management = args_dict['participant_to_algorithm_management']
        if participant_to_algorithm_management not in ['one_to_many','one_to_one']:
          error = "%s.initExp unsupported participant_to_algorithm_management: '%s'. Must be in {'one_to_many','one_to_one'}" % (self.app_id,participant_to_algorithm_management)
          return '{}',False,error

      # assign uid to each algorithm and save it
      for algorithm in alg_list:
        alg_uid = utils.getNewUID()
        algorithm['alg_uid'] = alg_uid

        db.set(app_id+':algorithms',alg_uid,'alg_uid',alg_uid)
        db.set(app_id+':algorithms',alg_uid,'exp_uid',exp_uid)

      db.set(app_id+':experiments',exp_uid,'exp_uid',exp_uid)
      db.set(app_id+':experiments',exp_uid,'app_id',app_id)
      db.set(app_id+':experiments',exp_uid,'n',n)
      db.set(app_id+':experiments',exp_uid,'failure_probability',delta)
      db.set(app_id+':experiments',exp_uid,'alg_list',alg_list)
      db.set(app_id+':experiments',exp_uid,'algorithm_management_settings',algorithm_management_settings)
      db.set(app_id+':experiments',exp_uid,'participant_to_algorithm_management',participant_to_algorithm_management)
      db.set(app_id+':experiments',exp_uid,'instructions',instructions)
      db.set(app_id+':experiments',exp_uid,'debrief',debrief)
      db.set(app_id+':experiments',exp_uid,'context_type',context_type)
      db.set(app_id+':experiments',exp_uid,'context',context)
      db.set(app_id+':experiments',exp_uid,'num_tries',num_tries)
      db.set(app_id+':experiments',exp_uid,'git_hash',git_hash)

      # now create intitialize each algorithm
      for algorithm in alg_list:
        alg_id = algorithm['alg_id'] 
        alg_uid = algorithm['alg_uid']

        db.set(app_id+':algorithms',alg_uid,'alg_id',alg_id)
        db.set(app_id+':algorithms',alg_uid,'alg_uid',alg_uid)
        db.set(app_id+':algorithms',alg_uid,'exp_uid',exp_uid)

        # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
        rc = ResourceClient(app_id,exp_uid,alg_uid,db)

        # get specific algorithm to make calls to 
        alg = utils.get_app_alg(self.app_id,alg_id)

        # call initExp
        didSucceed,dt = utils.timeit(alg.initExp)(resource=rc,n=n,failure_probability=delta)

        log_entry = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'initExp','duration':dt,'timestamp':utils.datetimeNow() } 
        ell.log( app_id+':ALG-DURATION', log_entry  )

      response_json = '{}'

      log_entry = { 'exp_uid':exp_uid,'task':'initExp','json':response_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return response_json,True,''

    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'initExp','error':error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error

  def getQuery(self,exp_uid,args_json,db,ell):
    """
    A request to ask which two arms to duel next

    Expected input (in jsonstructure with string keys):
      [optional] (string) participant_uid :  unique identifier of session for a participant answering questions (that is, an email address is not good enough as the participant could participate in multiple exp_uids so it would not be unique against all experiments), if key non-existant particpant_uid is assigned as exp_uid. 

    Expected output (in json structure with string keys):
      (list) target_indices : list that stores dictionary of targets with fields:
            { 
              (int) index : the index of the target of relevance
              (str) label : in {'left','right'} for display
              (int) flag : integer for algorithm's use
            }
      (str) query_uid : unique identifier of query (used to look up for processAnswer)

    Usage: 
      getQuery_response_json,didSucceed,message = app.getQuery(db_API,exp_uid,getQuery_args_json)

    Example input:
      getQuery_args_json = {"participant_uid": "0077110d03cf06b8f77d11acc399e8a7"}

    Example output:
      getQuery_response_json = {"query_uid": "4d02a9924f92138287edd17ca5feb6e1", "target_indices": [{"index": 9, "flag": 0, "label": "left"}, {"index": 8, "flag": 1, "label": "right"}]}

    """
    try: 
      app_id = self.app_id

      log_entry = { 'exp_uid':exp_uid,'task':'getQuery','json':args_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-CALL', log_entry  )

      # convert args_json to args_dict
      try:
        args_dict = json.loads(args_json)
      except:
        error = "%s.initExp input args_json is in improper format" % self.app_id
        return '{}',False,error

      # get list of algorithms associated with project
      alg_list,didSucceed,message = db.get(app_id+':experiments',exp_uid,'alg_list')
      alg_label_to_alg_id = {}
      alg_label_to_alg_uid = {}
      for algorithm in alg_list:
        alg_label_to_alg_id[ algorithm['alg_label'] ] = algorithm['alg_id']
        alg_label_to_alg_uid[ algorithm['alg_label'] ] = algorithm['alg_uid']

      algorithm_management_settings,didSucceed,message = db.get(app_id+':experiments',exp_uid,'algorithm_management_settings')

      # ASSIGN ALGORITHM TO PARTICIPANT
      if 'participant_uid' in args_dict:
        participant_uid = args_dict['participant_uid']
      else:
        participant_uid = exp_uid

      participant_doc_exists,didSucceed,message = db.exists(app_id+':participants',participant_uid,'participant_uid')
      first_participant_query = not participant_doc_exists
      if first_participant_query:
        db.set(app_id+':participants',participant_uid,'participant_uid',participant_uid)
        db.set(app_id+':participants',participant_uid,'exp_uid',exp_uid)

      participant_to_algorithm_management,didSucceed,message = db.get(app_id+':experiments',exp_uid,'participant_to_algorithm_management')
      if (participant_uid==exp_uid) or (participant_to_algorithm_management=='one_to_many') or (first_participant_query):

        if algorithm_management_settings['mode']=='fixed_proportions':
          proportions_list = algorithm_management_settings['params']['proportions']
          prop = [ prop_item['proportion'] for prop_item in proportions_list ]
          prop_item = numpy.random.choice(alg_list,p=prop)
        else:
          raise Exception('algorithm_management_mode : '+algorithm_management_settings['mode']+' not implemented')
        alg_id = alg_label_to_alg_id[ prop_item['alg_label'] ] 
        alg_uid = alg_label_to_alg_uid[ prop_item['alg_label'] ]
        alg_label = prop_item['alg_label']
        
        if (first_participant_query) and (participant_to_algorithm_management=='one_to_one'):
          db.set(app_id+':participants',participant_uid,'alg_id',alg_id)
          db.set(app_id+':participants',participant_uid,'alg_uid',alg_uid)

      elif (participant_to_algorithm_management=='one_to_one'):
        # If here, then alg_uid should already be assigned in participant doc
        alg_id,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_id')
        alg_uid,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_uid')
      else:
        raise Exception('participant_to_algorithm_management : '+participant_to_algorithm_management+' not implemented')

      # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
      rc = ResourceClient(app_id,exp_uid,alg_uid,db)

      # get specific algorithm to make calls to 
      alg = utils.get_app_alg(self.app_id,alg_id)

      # call getQuery
      index_left,index_right,index_painted,dt = utils.timeit(alg.getQuery)(resource=rc)

      # check for context
      context_type,didSucceed,message = db.get(app_id+':experiments',exp_uid,'context_type')
      context,didSucceed,message = db.get(app_id+':experiments',exp_uid,'context')

      # log
      log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'getQuery','duration':dt } 
      log_entry_durations.update( rc.getDurations() )
      meta = {'log_entry_durations':log_entry_durations}

      # create JSON query payload    
      if index_left==index_painted:
        targets = [ {'index':index_left,'label':'left','flag':1}, {'index':index_right,'label':'right','flag':0} ]
      else:
        targets = [ {'index':index_left,'label':'left','flag':0}, {'index':index_right,'label':'right','flag':1} ]
      timestamp = str(utils.datetimeNow())
      query_uid = utils.getNewUID()
      query = {}
      query['query_uid'] = query_uid
      query['target_indices'] = targets

      # save query data to database
      query_doc = {}
      query_doc.update(query)
      query_doc['participant_uid'] = participant_uid
      query_doc['alg_uid'] = alg_uid
      query_doc['exp_uid'] = exp_uid
      query_doc['alg_label'] = alg_label
      query_doc['timestamp_query_generated'] = timestamp
      db.set_doc(app_id+':queries',query_uid,query_doc)

      # add context after updating query doc to avoid redundant information
      query['context_type'] = context_type
      query['context'] = context

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

  def processAnswer(self,exp_uid,args_json,db,ell):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input (in json structure with string keys):
      (str) query_uid : unique identifier of query
      (int) index_winner : index of arm must be {index_left,index_right}

    Expected output (comma separated): 
      if error:
        return (JSON) '{}', (bool) False, (str) error
      else:
        return (JSON) '{}', (bool) True,''

    Usage:
      processAnswer_args_json,didSucceed,message = app.processAnswer(db_API,exp_uid,processAnswer_args_json)

    Example input:
      processAnswer_args_json = {"query_uid": "4d02a9924f92138287edd17ca5feb6e1", "index_winner": 8}

    Example output:
      processAnswer_response_json = {}
    """

    try:
      app_id = self.app_id

      log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','json':args_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-CALL', log_entry  )

      # convert args_json to args_dict
      try:
        args_dict = json.loads(args_json)
      except:
        error = "%s.processAnswer input args_json is in improper format" % self.app_id
        return '{}',False,error

      # check for the fields that must be contained in args or error occurs
      necessary_fields = ['index_winner','query_uid']
      for field in necessary_fields:
        try:
          args_dict[field]
        except KeyError:
          error = "%s.processAnswer input arguments missing field: %s" % (self.app_id,str(field)) 
          return '{}',False,error

      # get list of algorithms associated with project
      alg_list,didSucceed,message = db.get(app_id+':experiments',exp_uid,'alg_list')

      # get alg_id
      query_uid = args_dict['query_uid']
      alg_uid,didSucceed,message = db.get(app_id+':queries',query_uid,'alg_uid')
      for algorithm in alg_list:
        if alg_uid == algorithm['alg_uid']:
          alg_id = algorithm['alg_id']
          alg_label = algorithm['alg_label']
          num_reported_answers,didSucceed,message = db.increment(app_id+':experiments',exp_uid,'num_reported_answers_for_'+alg_uid)

      # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
      rc = ResourceClient(app_id,exp_uid,alg_uid,db)

      # get specific algorithm to make calls to 
      alg = utils.get_app_alg(self.app_id,alg_id)

      n,didSucceed,message = db.get(app_id+':experiments',exp_uid,'n')
      targets,didSucceed,message = db.get(app_id+':queries',query_uid,'target_indices')
      for target in targets:
        if target['label'] == 'left':
          index_left = target['index']
        if target['label'] == 'right':
          index_right = target['index']
        if target['flag'] == 1:
          index_painted = target['index']

      index_winner = args_dict['index_winner']
      query_meta = args_dict.get('query_meta',{})

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
      db.set(app_id+':queries',query_uid,'query_meta',query_meta)

      # call processAnswer
      didSucceed,dt = utils.timeit(alg.processAnswer)(resource=rc,index_left=index_left,index_right=index_right,index_painted=index_painted,index_winner=index_winner)

      log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'processAnswer','duration':dt } 
      log_entry_durations.update( rc.getDurations() )
      meta = {'log_entry_durations':log_entry_durations}

      ###############
      if num_reported_answers % ((n+4)/4) == 0:
        predict_id = 'arm_ranking'
        params = {'alg_label':alg_label}
        predict_args_dict = {'predict_id':predict_id,'params':params}
        predict_args_json = json.dumps(predict_args_dict)

        db.submit_job(app_id,exp_uid,'predict',predict_args_json,ignore_result=True)
      ###############

      response_args_dict = {}
      args_out = {'args':response_args_dict,'meta':meta}
      response_json = json.dumps(args_out)

      log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','json':response_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return response_json,True,""
    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','error':error,'timestamp':utils.datetimeNow(),'args_json':args_json }  
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error


  def predict(self,exp_uid,args_json,db,ell):
    """
    uses current model empirical estimates to forecast which index has the highest mean

    Expected input (in json structure with string keys):
      (string) predict_id : identifier for the desired prediction
      (list) params : dictionary of stat_id specific fields.


    ##########
    Description: uses current model empirical estimates to forecast the ranking of the arms in order of likelhood of being the best from most to least likely

    Expected input:
      (string) predict_id : 'arm_ranking'
      (dict) params : dictionary with fields
          (string) alg_label : describes target algorithm to use

    Expected output (in json structure):
      (list of dicts with fields):
        (int) index : index of target
        (int) rank : rank that the algorithm assigns to index (rank 0 is most likely the best arm)
    """

    try:
      app_id = self.app_id

      log_entry = { 'exp_uid':exp_uid,'task':'predict','json':args_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-CALL', log_entry  )

      # convert args_json to args_dict
      try:
        args_dict = json.loads(args_json)
      except:
        error = "%s.predict failed to convert input args_json due to improper format" %(self.app_id) 
        return '{}',False,error

      # check for the fields that must be contained in args or error occurs
      necessary_fields = ['predict_id','params']
      for field in necessary_fields:
        try:
          args_dict[field]
        except KeyError:
          error = "%s.predict input arguments missing field: %s" % (self.app_id,str(field)) 
          return '{}',False,error

      predict_id = args_dict['predict_id']
      params = args_dict['params']

      if predict_id == "arm_ranking":

        alg_label = params['alg_label']

        # get list of algorithms associated with project
        alg_list,didSucceed,message = db.get(app_id+':experiments',exp_uid,'alg_list')

        # get alg_id
        for algorithm in alg_list:
          if alg_label == algorithm['alg_label']:
            alg_id = algorithm['alg_id']
            alg_uid = algorithm['alg_uid']
            num_reported_answers,didSucceed,message = db.get(app_id+':experiments',exp_uid,'num_reported_answers_for_'+alg_uid)
            if type(num_reported_answers)!=int:
              num_reported_answers=0


        # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
        rc = ResourceClient(app_id,exp_uid,alg_uid,db)

        # get specific algorithm to make calls to 
        alg = utils.get_app_alg(self.app_id,alg_id)

        # call getQuery
        scores,precisions,dt = utils.timeit(alg.predict)(resource=rc)

        log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'predict','duration':dt } 
        log_entry_durations.update( rc.getDurations() )
        meta = {'log_entry_durations':log_entry_durations}

        import numpy
        ranks = (-numpy.array(scores)).argsort().tolist()

        n = len(scores)
        indexes = numpy.array(range(n))[ranks]
        scores = numpy.array(scores)[ranks]
        precisions = numpy.array(precisions)[ranks]
        ranks = range(n)

        targets = []
        for index in range(n):
          targets.append( {'index':indexes[index],'rank':ranks[index],'score':scores[index],'precision':precisions[index]} )

        log_entry = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'timestamp':utils.datetimeNow() } 
        log_entry.update( {'targets':targets,'num_reported_answers':num_reported_answers} )

        ell.log( app_id+':ALG-EVALUATION', log_entry  )

        response_args_dict = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'targets':targets,'num_reported_answers':num_reported_answers}

      args_out = {'args':response_args_dict,'meta':meta}
      predict_json = json.dumps(args_out)

      log_entry = { 'exp_uid':exp_uid,'task':'predict','json':predict_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return predict_json,True,''
    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'predict','error':str(error),'timestamp':utils.datetimeNow(),'args_json':args_json }  
      didSucceed,message = ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error
    

  def getStats(self,exp_uid,args_json,db,ell):
    """
    Get statistics for the experiment and its algorithms

    Expected input (in json structure with string keys):
      (string) stat_id : identifier for the desired statistic
      (dict) params : dictionary of stat_id specific fields.

    See Next.utils.get_app_supported_stats(app_id) ResourceManager.get_app_supported_stats(app_id)
    for a description of each of the available stats and their inputs and outputs
    """

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
      necessary_fields = ['stat_id','params']
      for field in necessary_fields:
        try:
          args_dict[field]
        except KeyError:
          error = "%s.getStats input arguments missing field: %s" % (self.app_id,str(field)) 
          return '{}',False,error

      stat_id = args_dict['stat_id']
      params = args_dict['params']

      dashboard = DuelingBanditsPureExplorationDashboard(db,ell)

      # input task
      if stat_id == "api_activity_histogram":
        task = params['task']
        activity_stats = dashboard.api_activity_histogram(self.app_id,exp_uid,task)
        stats = activity_stats

      # input Noneokay
      elif stat_id == "api_processAnswer_activity_stacked_histogram":
        activity_stats = dashboard.api_processAnswer_activity_stacked_histogram(self.app_id,exp_uid)
        stats = activity_stats

      # input task
      elif stat_id == "compute_duration_multiline_plot":
        task = params['task']
        compute_stats = dashboard.compute_duration_multiline_plot(self.app_id,exp_uid,task)
        stats = compute_stats

      # input task, alg_label
      elif stat_id == "compute_duration_detailed_stacked_area_plot":
        task = params['task']
        alg_label = params['alg_label']
        compute_detailed_stats = dashboard.compute_duration_detailed_stacked_area_plot(self.app_id,exp_uid,task,alg_label)
        stats = compute_detailed_stats
        
      # input alg_label
      elif stat_id == "response_time_histogram":
        alg_label = params['alg_label']
        response_time_stats = dashboard.response_time_histogram(self.app_id,exp_uid,alg_label)
        stats = response_time_stats

           # input alg_label
      elif stat_id == "network_delay_histogram":
        alg_label = params['alg_label']
        network_delay_stats = dashboard.network_delay_histogram(self.app_id,exp_uid,alg_label)
        stats = network_delay_stats


      elif stat_id == "most_current_ranking":
        alg_label = params['alg_label']
        stats = dashboard.most_current_ranking(self.app_id,exp_uid,alg_label)

      response_json = json.dumps(stats)

      log_entry = { 'exp_uid':exp_uid,'task':'getStats','json':response_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return response_json,True,''
    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'getStats','error':error,'timestamp':utils.datetimeNow(),'args_json':args_json } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error


