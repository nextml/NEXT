import json
import numpy
import numpy.random
from datetime import datetime
from datetime import timedelta
from next.utils import utils

import matplotlib
matplotlib.use('Agg')

MAX_SAMPLES_PER_PLOT = 100

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
      (dict) MPLD3 plot dictionary
    """


    list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':APP-CALL',{'exp_uid':exp_uid,'task':task})

    from datetime import datetime
    from datetime import timedelta
    start_date_str,didSucceed,message = self.db.get('experiments_admin',exp_uid,'start_date')
    start_date = utils.str2datetime(start_date_str)
    numerical_timestamps = [ ( utils.str2datetime(item['timestamp'])-start_date).total_seconds() for item in list_of_log_dict]

    import matplotlib.pyplot as plt
    import mpld3
    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#FFFFFF'),figsize=(12,1.5))
    ax.hist(numerical_timestamps,min(int(1+4*numpy.sqrt(len(numerical_timestamps))),300),alpha=0.5,color='black')
    ax.set_frame_on(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(0, max(numerical_timestamps))
    plot_dict = mpld3.fig_to_dict(fig)
    plt.close()

    
    return plot_dict



  def compute_duration_multiline_plot(self,app_id,exp_uid,task):
    """
    Description: Returns multiline plot where there is a one-to-one mapping lines to 
    algorithms and each line indicates the durations to complete the task (wrt to the api call) 

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
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
      
      x = numpy.array(x)
      y = numpy.array(y)
      t = numpy.array(t)
      num_items = len(list_of_log_dict)
      multiplier = min(num_items,MAX_SAMPLES_PER_PLOT)
      incr_inds = [ k*num_items/multiplier for k in range(multiplier)]
      max_inds = list(numpy.argsort(-y)[0:multiplier])
      final_inds = sorted(set(incr_inds + max_inds))
      x = list(x[final_inds])
      y = list(y[final_inds])
      t = list(t[final_inds])


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


    import matplotlib.pyplot as plt
    import mpld3
    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#EEEEEE'))
    for alg_dict in list_of_alg_dicts:
        ax.plot(alg_dict['x'],alg_dict['y'],label=alg_dict['legend_label'])
    ax.set_xlabel('API Call')
    ax.set_ylabel('Duration (s)')
    ax.set_xlim([x_min,x_max])
    ax.set_ylim([y_min,y_max])
    ax.grid(color='white', linestyle='solid')
    ax.set_title(task, size=14)
    legend = ax.legend(loc=2,ncol=3,mode="expand")
    for label in legend.get_texts():
      label.set_fontsize('small')
    plot_dict = mpld3.fig_to_dict(fig)
    plt.close()


    return plot_dict


  def compute_duration_detailed_stacked_area_plot(self,app_id,exp_uid,task,alg_label,detailedDB=False):
    """
    Description: Returns stacked area plot for a particular algorithm and task where the durations
    are broken down into compute,db_set,db_get (for cpu, database_set, database_get)

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
    """

    alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

    for algorithm in alg_list:
      if algorithm['alg_label'] == alg_label:
        alg_id = algorithm['alg_id']
        alg_uid = algorithm['alg_uid']

    list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':ALG-DURATION',{'alg_uid':alg_uid,'task':task})
    list_of_log_dict = sorted(list_of_log_dict, key=lambda item: utils.str2datetime(item['timestamp']) )


    y = []
    for item in list_of_log_dict:
      y.append( item.get('app_duration',0.) + item.get('duration_enqueued',0.) )
    y = numpy.array(y)
    num_items = len(list_of_log_dict)
    multiplier = min(num_items,MAX_SAMPLES_PER_PLOT)
    incr_inds = [ k*num_items/multiplier for k in range(multiplier)]
    max_inds = list(numpy.argsort(-y)[0:multiplier])
    final_inds = sorted(set(incr_inds + max_inds))


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
    for idx in final_inds:
      item = list_of_log_dict[idx]
      x.append(idx+1)
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

    try:
      min_x = min(x)
      max_x = max(x)
    except:
      min_x = 0.
      max_x = 0.

    import matplotlib.pyplot as plt
    import mpld3
    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#EEEEEE'))
    stack_coll = ax.stackplot(x,compute,dbGet,dbSet,admin,enqueued, alpha=.5)
    ax.set_xlabel('API Call')
    ax.set_ylabel('Duration (s)')
    ax.set_xlim([min_x,max_x])
    ax.set_ylim([0.,max_y_value])
    ax.grid(color='white', linestyle='solid')
    ax.set_title(alg_label+' - '+task, size=14)
    proxy_rects = [plt.Rectangle((0, 0), 1, 1, alpha=.5,fc=pc.get_facecolor()[0]) for pc in stack_coll]
    legend = ax.legend(proxy_rects, ['compute','dbGet','dbSet','admin','enqueued'],loc=2,ncol=3,mode="expand")
    for label in legend.get_texts():
      label.set_fontsize('small')
    plot_dict = mpld3.fig_to_dict(fig)
    plt.close()
    

    return plot_dict


  def response_time_histogram(self,app_id,exp_uid,alg_label):
    """
    Description: returns the data to plot response time histogram of processAnswer for each algorithm  

    Expected input:
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
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

    import matplotlib.pyplot as plt
    import mpld3
    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#FFFFFF'))
    ax.hist(t,MAX_SAMPLES_PER_PLOT,range=(0,30),alpha=0.5,color='black')
    ax.set_xlim(0, 30)
    ax.set_axis_off()
    ax.set_xlabel('Durations (s)')
    ax.set_ylabel('Count')
    ax.set_title(alg_label + " - response time", size=14)
    plot_dict = mpld3.fig_to_dict(fig)
    plt.close()

    return plot_dict

  def network_delay_histogram(self,app_id,exp_uid,alg_label):
    """
    Description: returns the data to network delay histogram of the time it takes to getQuery+processAnswer for each algorithm  

    Expected input:
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
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

    import matplotlib.pyplot as plt
    import mpld3
    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#FFFFFF'))
    ax.hist(t,MAX_SAMPLES_PER_PLOT,range=(0,5),alpha=0.5,color='black')
    ax.set_xlim(0, 5)
    ax.set_axis_off()
    ax.set_xlabel('Durations (s)')
    ax.set_ylabel('Count')
    ax.set_title(alg_label + " - network delay", size=14)
    plot_dict = mpld3.fig_to_dict(fig)
    plt.close()

    return plot_dict

