"""
PoolBasedTripletMDS

This module manages the execution of different algorithms implemented to solve the 
problem described in PoolBasedTripletMDSPrototype.py. See this file for
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
from next.apps.PoolBasedTripletMDS.dashboard.Dashboard import PoolBasedTripletMDSDashboard

class PoolBasedTripletMDS(AppPrototype):

  def __init__(self): 
    self.app_id = 'PoolBasedTripletMDS'

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
      rc = ResourceClient(app_id,exp_uid,alg_uid,db)

      # get specific algorithm to make calls to 
      alg = utils.get_app_alg(self.app_id,alg_id)

      didSucceed,dt = utils.timeit(alg.daemonProcess)(resource=rc,daemon_args_dict=alg_daemon_args)
      
      log_entry = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'daemonProcess','duration':dt,'timestamp':utils.datetimeNow() } 
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
      log_entry = { 'exp_uid':exp_uid,'task':'daemonProcess','error':error,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error


  def initExp(self,exp_uid,args_json,db,ell):
    """
    initialize the project and necessary experiments 

    Expected input (in json structure with string keys):
      (int) n : number of objects
      (int) d : desired dimension (can be changed later) 
      (float) failure_probability : confidence
      [optional] (list of dicts) alg_list : with fields (Defaults given by Info.get_app_default_alg_list)
            (string) alg_id : valid alg_id for this app_id
            (string) alg_label : unique identifier for algorithm (e.g. may have experiment with repeated alg_id's, but alg_labels must be unqiue, will also be used for plot legends
            [optional] (string) test_alg_label : must be one of the alg_label's in alg_list (Default is self)
            [optional] (dict) params : algorithm-specific parameters
      [optional] (dict) algorithm_management_settings : dictionary with fields (string) 'mode' and (dict) 'params'. mode in {'pure_exploration','explore_exploit','fixed_proportions'}. Default is 'fixed_proportions' and allocates uniform probability to each algorithm. If mode=fixed_proportions then params is a dictionary that contains the field 'proportions' which is a list of dictionaries with fields 'alg_label' and 'proportion' for all algorithms in alg_list. All proportions must be positive and sum to 1 over all algs in alg_list 
      [optional] (string) participant_to_algorithm_management : in {'one_to_one','one_to_many'}. Default is 'one_to_many'.
      [optional] (string) instructions
      [optional] (string) debrief
      [optional] (int) num_tries
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
      necessary_fields = ['n','d','failure_probability']
      for field in necessary_fields:
        try:
          args_dict[field]
        except KeyError:
          error = "%s.initExp input arguments missing field: %s" % (self.app_id,str(field)) 
          return '{}',False,error

      n = args_dict['n']
      d = args_dict['d']
      delta = args_dict['failure_probability']

      # ALG LIST FORMATTING CHECK
      if 'alg_list' in args_dict:
        alg_list = args_dict['alg_list']
        supportedAlgs = utils.get_app_supported_algs(self.app_id)
        for algorithm in alg_list:
          if algorithm['alg_id'] not in supportedAlgs:
            error = "%s.initExp unsupported algorithm '%s' in alg_list" % (self.app_id,algorithm['alg_id'])
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
        alg_id = algorithm['alg_id'] 
        alg_uid = utils.getNewUID()
        algorithm['alg_uid'] = alg_uid

        db.set(app_id+':algorithms',alg_uid,'alg_id',alg_id)
        db.set(app_id+':algorithms',alg_uid,'alg_uid',alg_uid)
        db.set(app_id+':algorithms',alg_uid,'exp_uid',exp_uid)
      
      db.set(app_id+':experiments',exp_uid,'exp_uid',exp_uid)
      db.set(app_id+':experiments',exp_uid,'app_id',app_id)
      db.set(app_id+':experiments',exp_uid,'n',n)
      db.set(app_id+':experiments',exp_uid,'d',d)
      db.set(app_id+':experiments',exp_uid,'failure_probability',delta)
      db.set(app_id+':experiments',exp_uid,'alg_list',alg_list)
      db.set(app_id+':experiments',exp_uid,'algorithm_management_settings',algorithm_management_settings)
      db.set(app_id+':experiments',exp_uid,'participant_to_algorithm_management',participant_to_algorithm_management)
      db.set(app_id+':experiments',exp_uid,'instructions',instructions)
      db.set(app_id+':experiments',exp_uid,'debrief',debrief)
      db.set(app_id+':experiments',exp_uid,'num_tries',num_tries)
      db.set(app_id+':experiments',exp_uid,'git_hash',git_hash)
      
      # now create intitialize each algorithm
      for algorithm in alg_list:
        alg_id = algorithm['alg_id'] 
        alg_uid = algorithm['alg_uid']
        params = algorithm.get('params',None)
        params['num_tries']=num_tries

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
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'initExp','error':error,'timestamp':utils.datetimeNow() } 
      print log_entry
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error


  def getQuery(self,exp_uid,args_json,db,ell):
    """
    A request to ask the query: "is {center} more similar to {left} or {right}?"

    Expected input (in jsonstructure with string keys):
      [optional] (string) participant_uid :  unique identifier of session for a participant answering questions (that is, an email address is not good enough as the participant could participate in multiple exp_uids so it would not be unique against all experiments), if key non-existant particpant_uid is assigned as exp_uid. 
    
    Expected output (in json structure with string keys): 
      (list) target_indices : list that stores dictionary of targets with fields:
            { 
              (int) index : the index of the target of relevance
              (str) label : in {'left','right','center'} 
              (int) flag : integer for algorithm's use
            }
      (str) query_uid : unique identifier of query (used to look up for processAnswer)
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
          db.set(app_id+':participants',participant_uid,'alg_label',alg_label)

      elif (participant_to_algorithm_management=='one_to_one'):
        # If here, then alg_uid should already be assigned in participant doc
        alg_id,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_id')
        alg_uid,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_uid')
        alg_label,didSucceed,message = db.get(app_id+':participants',participant_uid,'alg_label')
      else:
        raise Exception('participant_to_algorithm_management : '+participant_to_algorithm_management+' not implemented')

      # figure out which queries have already been asked
      queries,didSucceed,message = db.get_docs_with_filter(app_id+':queries',{'participant_uid':participant_uid})
      do_not_ask_list = []
      for q in queries:
        h = [-1,-1,-1]
        for t in q.get('target_indices',[]):
          if t['label']=='center':
            h[2] = t['index']
          elif t['label']=='left':
            h[0] = t['index']
          elif t['label']=='right':
            h[1] = t['index']
        do_not_ask_list.append(h)

      # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
      rc = ResourceClient(app_id,exp_uid,alg_uid,db)

      # get specific algorithm to make calls to 
      alg = utils.get_app_alg(self.app_id,alg_id)

      # call getQuery
      index_center,index_left,index_right,dt = utils.timeit(alg.getQuery)(resource=rc,do_not_ask_list=do_not_ask_list)

      log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'getQuery','duration':dt } 
      log_entry_durations.update( rc.getDurations() )
      meta = {'log_entry_durations':log_entry_durations}

      # create JSON query payload
      timestamp = str(utils.datetimeNow())
      query_uid = utils.getNewUID()
      query = {}
      query['query_uid'] = query_uid
      query['target_indices'] = [ {'index':index_center,'label':'center','flag':0},{'index':index_left,'label':'left','flag':0},{'index':index_right,'label':'right','flag':0} ]
  
      # save query data to database
      query_doc = {}
      query_doc.update(query)
      query_doc['participant_uid'] = participant_uid
      query_doc['alg_uid'] = alg_uid
      query_doc['exp_uid'] = exp_uid
      query_doc['alg_label'] = alg_label
      query_doc['timestamp_query_generated'] = timestamp
      for field in query_doc:
        db.set(app_id+':queries',query_uid,field,query_doc[field])

      args_out = {'args':query,'meta':meta}
      response_json = json.dumps(args_out)

      log_entry = { 'exp_uid':exp_uid,'task':'getQuery','json':response_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return response_json,True,''
    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'getQuery','error':error,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error

  def processAnswer(self,exp_uid,args_json,db,ell):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input (in json structure with string keys):
      (index) index_winner : index of the winner in (must be index of left or right target in target_indices)
      (str) query_uid : unique identifier of query

    Expected output (comma separated): 
      if error:
        return (JSON) '{}', (bool) False, (str) error
      else:
        return (JSON) '{}', (bool) True,''
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

      targets,didSucceed,message = db.get(app_id+':queries',query_uid,'target_indices')
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
      q = [index_left,index_right,index_center]
      if index_winner==index_right:
        q = [index_right,index_left,index_center]
      db.set(app_id+':queries',query_uid,'q',q)

      # call processAnswer
      didSucceed,dt = utils.timeit(alg.processAnswer)(resource=rc,index_center=index_center,index_left=index_left,index_right=index_right,index_winner=index_winner)

      log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'processAnswer','duration':dt } 
      log_entry_durations.update( rc.getDurations() )
      meta = {'log_entry_durations':log_entry_durations}

      
      # check if we're going to evaluate this loss
      n,didSucceed,message = db.get(app_id+':experiments',exp_uid,'n')
      
      if num_reported_answers % ((n+4)/4) == 0:
        predict_id = 'get_embedding'
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
      log_entry = { 'exp_uid':exp_uid,'task':'processAnswer','error':error,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error


  def predict(self,exp_uid,args_json,db,ell):
    """
    Have the model learned by some particular algorithm predict a variety of stuff 

    Expected input (in json structure with string keys):
      (string) predict_id : identifier for the desired prediction
      (list) params : dictionary of stat_id specific fields.


    ##########
    Description: Each algorithm (with an associated alg_label) has a test_alg_label associated with it. 

    Expected input:
      (string) predict_id : 'evaluate_on_test'
      (dict) params : dictionary with fields
          (string) alg_label : describes target algorithm to test
          (string) test_alg_label : describes the algorithm that whos triplets are evaluated on the target algorithm

    Expected output (in json structure):
      (float) num_reported_answers : number of reported answers after which the calculation was made
      (float) error : 0/1 loss on test set
    """

    try:
      app_id = self.app_id

      log_entry = { 'exp_uid':exp_uid,'task':'predict','json':args_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-CALL', log_entry  )

      # convert args_json to args_dict
      try:
        args_dict = json.loads(args_json)
      except:
        error = "%s.predict input args_json is in improper format" % self.app_id
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

      alg_label = params['alg_label']

      # get list of algorithms associated with project
      alg_list,didSucceed,message = db.get(app_id+':experiments',exp_uid,'alg_list')
      
      # get alg_id
      for algorithm in alg_list:
        if alg_label == algorithm['alg_label']:
          alg_id = algorithm['alg_id']
          alg_uid = algorithm['alg_uid']

      meta = {}
      if predict_id=='get_embedding':

        # get sandboxed database for the specific app_id,alg_id,exp_uid - closing off the rest of the database to the algorithm
        rc = ResourceClient(app_id,exp_uid,alg_uid,db)

        # get specific algorithm to make calls to 
        alg = utils.get_app_alg(self.app_id,alg_id)

        ##### Get Embedding #####
        Xd,num_reported_answers,dt = utils.timeit(alg.predict)(rc)

        log_entry_durations = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'task':'predict','duration':dt } 
        log_entry_durations.update( rc.getDurations() )
        meta = {'log_entry_durations':log_entry_durations}

        params['Xd'] = Xd
        params['num_reported_answers'] = num_reported_answers

        log_entry = { 'exp_uid':exp_uid,'alg_uid':alg_uid,'timestamp':utils.datetimeNow() } 
        log_entry.update( params )

        ell.log( app_id+':ALG-EVALUATION', log_entry  )

        params['timestamp'] = str(log_entry['timestamp'])
        response_args_dict = params

      elif predict_id=='get_queries':

        # get list of triplets from test
        queries,didSucceed,message = db.get_docs_with_filter(app_id+':queries',{'alg_uid':alg_uid})

        S = []
        for query in queries:
          if 'q' in query.keys():
            q = query['q']
            S.append(q)

        params['queries'] = S
        params['num_reported_answers'] = len(S)
        response_args_dict = params


      args_out = {'args':response_args_dict,'meta':meta}
      predict_json = json.dumps(args_out)

      log_entry = { 'exp_uid':exp_uid,'task':'predict','json':predict_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )

      return predict_json,True,''
    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'predict','error':str(error),'timestamp':utils.datetimeNow() } 
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

      dashboard = PoolBasedTripletMDSDashboard(db,ell)

      # input task
      if stat_id == "api_activity_histogram":
        task = params['task']
        activity_stats = dashboard.api_activity_histogram(self.app_id,exp_uid,task)
        stats = activity_stats

      # input None
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

      # input None
      elif stat_id == "test_error_multiline_plot":
        stats = dashboard.test_error_multiline_plot(self.app_id,exp_uid)

      # input alg_label
      elif stat_id == "most_current_embedding":
        alg_label = params['alg_label']
        stats = dashboard.most_current_embedding(self.app_id,exp_uid,alg_label)

      else:
        raise Exception('No valid stat_id provided')


      response_json = json.dumps(stats)

      log_entry = { 'exp_uid':exp_uid,'task':'getStats','json':response_json,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-RESPONSE', log_entry  )


      return response_json,True,''
    except Exception, err:
      error = traceback.format_exc()
      log_entry = { 'exp_uid':exp_uid,'task':'getStats','error':error,'timestamp':utils.datetimeNow() } 
      ell.log( app_id+':APP-EXCEPTION', log_entry  )
      return '{}',False,error
