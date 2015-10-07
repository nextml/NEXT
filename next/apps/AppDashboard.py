"""
StochasticBanditsPureExplorationDashboard 
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 2/11/2015

######################################
AppDashboard
"""


import json
import numpy
import numpy.random
from datetime import datetime
from datetime import timedelta
from next.utils import utils

class AppDashboard(object):

  def __init__(self,db,ell):
    self.db = db
    self.ell = ell

  def get_supported_stats(self):
    """
    Returns a list of dictionaries describing the identifier (stat_id) and 
    necessary params inputs to be used when calling getStats

    Expected output (list of dicts, each with fields):
      (string) stat_id : the identiifer of the statistic
      (string) description : docstring of describing outputs
      (list of string) necessary_params : list where each string describes the type of param input like 'alg_label' or 'task'
    """

    stat_list = []

    stat = {}
    stat['stat_id'] = 'api_activity_histogram'
    stat['description'] = self.api_activity_histogram.__doc__
    stat['necessary_params'] = ['task']
    stat_list.append(stat)

    # stat = {}
    # stat['stat_id'] = 'api_processAnswer_activity_stacked_histogram'
    # stat['description'] = self.api_processAnswer_activity_stacked_histogram.__doc__
    # stat['necessary_params'] = []
    # stat_list.append(stat)

    stat = {}
    stat['stat_id'] = 'compute_duration_multiline_plot'
    stat['description'] = self.compute_duration_multiline_plot.__doc__
    stat['necessary_params'] = ['task']
    stat_list.append(stat)

    stat = {}
    stat['stat_id'] = 'compute_duration_detailed_stacked_area_plot'
    stat['description'] = self.compute_duration_detailed_stacked_area_plot.__doc__
    stat['necessary_params'] = ['task','alg_label']
    stat_list.append(stat)

    stat = {}
    stat['stat_id'] = 'response_time_histogram'
    stat['description'] = self.response_time_histogram.__doc__
    stat['necessary_params'] = ['alg_label']
    stat_list.append(stat)

    stat = {}
    stat['stat_id'] = 'network_time_histogram'
    stat['description'] = self.response_time_histogram.__doc__
    stat['necessary_params'] = ['alg_label']
    stat_list.append(stat)


    return stat_list  

  def api_activity_histogram(self,app_id,exp_uid,task):
    """
    Description: returns the data to plot all API activity (for all algorithms) in a histogram with respect to time for any task in {getQuery,processAnswer,predict} 

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}

    Expected output (in dict):
      (string) plot_type : 'histogram'
      (string) x_label : 'Date'
      (string) y_label : 'Count'
      (list) t : list of timestamp strings
      (string) legend_label : 'API Calls to '+task
    """


    list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':APP-CALL',{'exp_uid':exp_uid,'task':task})

    t = []
    for item in list_of_log_dict:
      t.append(str(item['timestamp'])[:-3])

    data = {}
    data['legend_label'] = 'API Calls to '+task
    data['t'] = t

    return_dict = {}
    return_dict['data'] = data
    return_dict['plot_type'] = 'histogram'
    return_dict['x_label'] = 'Date'
    return_dict['y_label'] = 'Count'
    
    return return_dict



  def compute_duration_multiline_plot(self,app_id,exp_uid,task):
    """
    Description: Returns multiline plot where there is a one-to-one mapping lines to 
    algorithms and each line indicates the durations to complete the task (wrt to the api call) 

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}

    Expected output (in dict):
      plot_type 'multi_line_plot'
      (string) x_label : 'API Call'
      (float) x_min : 1
      (float) x_max : maximum number of reported answers for any algorithm
      (string) y_label : 'Duration (s)'
      (float) y_min : 0.
      (float) y_max : maximum duration value achieved by any algorithm
      (list of dicts with fields) data : 
        (list of strings) t : list of timestamp strings
        (list of floats) x : integers ranging from 1 to maximum number of elements in y (or t)
        (list of floats) y : list of durations
        (string) legend_label : alg_label
    """
    alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

    x_min = numpy.float('inf')
    x_max = -numpy.float('inf')
    y_min = numpy.float('inf')
    y_max = -numpy.float('inf')
    list_of_alg_dicts = []

    for algorithm in alg_list:
      alg_id = algorithm['alg_id']
      alg_uid = algorithm['alg_uid']
      alg_label = algorithm['alg_label']
      
      list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':ALG-DURATION',{'alg_uid':alg_uid,'task':task})
      list_of_log_dict = sorted(list_of_log_dict, key=lambda item: utils.str2datetime(item['timestamp']) )

      x = []
      y = []
      t = []
      k=0
      for item in list_of_log_dict:
        k+=1
        x.append(k)
        y.append( item.get('app_duration',0.) + item.get('duration_enqueued',0.) )

        t.append(str(item['timestamp'])[:-3])


      alg_dict = {}
      alg_dict['legend_label'] = alg_label
      alg_dict['x'] = x
      alg_dict['y'] = y
      alg_dict['t'] = t
      try:
        x_min = min(x_min,min(x))
        x_max = max(x_max,max(x))
        y_min = min(y_min,min(y))
        y_max = max(y_max,max(y))
      except:
        pass

      list_of_alg_dicts.append(alg_dict)

    return_dict = {}
    return_dict['data'] = list_of_alg_dicts
    return_dict['plot_type'] = 'multi_line_plot'
    return_dict['x_label'] = 'API Call'
    return_dict['x_min'] = x_min
    return_dict['x_max'] = x_max
    return_dict['y_label'] = 'Duration (s)'
    return_dict['y_min'] = y_min
    return_dict['y_max'] = y_max
    
    return return_dict


  def compute_duration_detailed_stacked_area_plot(self,app_id,exp_uid,task,alg_label,detailedDB=False):
    """
    Description: Returns stacked area plot for a particular algorithm and task where the durations
    are broken down into compute,db_set,db_get (for cpu, database_set, database_get)

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

    Expected output (in dict):
      plot_type 'stacked_area_plot'
      (string) x_label : 'API Call'
      (float) x_min : 1
      (float) x_max : length of datastream
      (string) y_label : 'Duration (s)'
      (float) y_min : 0.
      (float) y_max : maximum duration value achieved sum of all layers
      (list of strings) t : list of timestamp strings
      (list of floats) x : integers ranging from 1 x_max
      (list of dicts with fields) data : 
        (list of floats) y : list of durations
        (string) legend_label : area_label in {'compute','db_set','db_get'}
    """

    alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

    for algorithm in alg_list:
      if algorithm['alg_label'] == alg_label:
        alg_id = algorithm['alg_id']
        alg_uid = algorithm['alg_uid']

    list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':ALG-DURATION',{'alg_uid':alg_uid,'task':task})
    list_of_log_dict = sorted(list_of_log_dict, key=lambda item: utils.str2datetime(item['timestamp']) )

    x = []
    t = []
    enqueued = []
    admin = []
    dbOverhead = []
    dbGet = []
    dbSet = []
    compute = []

    max_y_value = 0.
    min_y_value = float('inf')
    k = 0
    for item in list_of_log_dict:
      k += 1
      x.append(k)
      t.append(str(item.get('timestamp','')))

      _alg_duration = item.get('duration',0.)
      _alg_duration_dbGet = item.get('duration_dbGet',0.)
      _alg_duration_dbSet = item.get('duration_dbSet',0.)
      _duration_enqueued = item.get('duration_enqueued',0.)
      _app_duration = item.get('app_duration',0.)

      if (_app_duration+_duration_enqueued) > max_y_value:
        max_y_value = _app_duration + _duration_enqueued
      if (_app_duration+_duration_enqueued) < min_y_value:
        min_y_value = _app_duration + _duration_enqueued
      
      enqueued.append(_duration_enqueued)
      admin.append(_app_duration-_alg_duration)
      dbSet.append(_alg_duration_dbSet)
      dbGet.append(_alg_duration_dbGet)
      compute.append( _alg_duration - _alg_duration_dbSet - _alg_duration_dbGet )

    
    list_of_dicts = []

    duration_dict = {}
    duration_dict['legend_label'] = 'compute'
    duration_dict['y'] = compute
    list_of_dicts.append(duration_dict)

    duration_dict = {}
    duration_dict['legend_label'] = 'db:get'
    duration_dict['y'] = dbGet
    list_of_dicts.append(duration_dict)

    duration_dict = {}
    duration_dict['legend_label'] = 'db:set'
    duration_dict['y'] = dbSet
    list_of_dicts.append(duration_dict)

    duration_dict = {}
    duration_dict['legend_label'] = 'admin'
    duration_dict['y'] = admin
    list_of_dicts.append(duration_dict)

    duration_dict = {}
    duration_dict['legend_label'] = 'enqueued'
    duration_dict['y'] = enqueued
    list_of_dicts.append(duration_dict)

    return_dict = {}
    return_dict['x'] = x
    return_dict['t'] = t
    return_dict['data'] = list_of_dicts
    return_dict['plot_type'] = 'stacked_area_plot'
    return_dict['x_label'] = 'API Call'
    try:
      return_dict['x_min'] = min(x)
      return_dict['x_max'] = max(x)
      return_dict['y_min'] = min_y_value
      return_dict['y_max'] = max_y_value
    except:
      return_dict['x_min'] = 0.
      return_dict['x_max'] = 0.
      return_dict['y_min'] = 0.
      return_dict['y_max'] = 0.
    return_dict['y_label'] = 'Duration (s)'
    

    return return_dict


  def response_time_histogram(self,app_id,exp_uid,alg_label):
    """
    Description: returns the data to plot response time histogram of processAnswer for each algorithm  

    Expected input:
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

    Expected output (in dict):
      (string) plot_type : 'histogram'
      (string) x_label : 'Response Time'
      (string) y_label : 'Count'
      (string) legend_label : ''
    """

    alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

    for algorithm in alg_list:
      if algorithm['alg_label'] == alg_label:
        alg_id = algorithm['alg_id']
        alg_uid = algorithm['alg_uid']

    list_of_query_dict,didSucceed,message = self.db.get_docs_with_filter(app_id+':queries',{'exp_uid':exp_uid,'alg_uid':alg_uid})

    t = []
    for item in list_of_query_dict:
      try:
        t.append(item['response_time'])
      except:
        pass


    data = {}
    data['legend_label'] = 'Response Time '
    data['t'] = t

    return_dict = {}
    return_dict['data'] = data
    return_dict['plot_type'] = 'histogram_real'
    return_dict['x_label'] = 'Durations'
    return_dict['y_label'] = 'Count'
    
    return return_dict

  def network_delay_histogram(self,app_id,exp_uid,alg_label):
    """
    Description: returns the data to network delay histogram of the time it takes to getQuery+processAnswer for each algorithm  

    Expected input:
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

    Expected output (in dict):
      (string) plot_type : 'histogram'
      (string) x_label : 'Network Delay'
      (string) y_label : 'Count'
      (string) legend_label : ''
    """

    alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

    for algorithm in alg_list:
      if algorithm['alg_label'] == alg_label:
        alg_id = algorithm['alg_id']
        alg_uid = algorithm['alg_uid']

    list_of_query_dict,didSucceed,message = self.db.get_docs_with_filter(app_id+':queries',{'exp_uid':exp_uid,'alg_uid':alg_uid})

    t = []
    for item in list_of_query_dict:
      try:
        t.append(item['network_delay'])
      except:
        pass


    data = {}
    data['legend_label'] = 'Network Delay'
    data['t'] = t

    return_dict = {}
    return_dict['data'] = data
    return_dict['plot_type'] = 'histogram_real'
    return_dict['x_label'] = 'Delays'
    return_dict['y_label'] = 'Count'
    
    return return_dict

