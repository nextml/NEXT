import json
import numpy
import numpy.random
from datetime import datetime
from datetime import timedelta
import next.utils as utils

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mpld3
import cPickle as pickle
import os
import pandas as pd
import io
import next.assistant.s3 as s3
import next.constants as constants
import apps.PoolBasedBinaryClassification.algs.LogisticRegressionActive as lr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


MAX_SAMPLES_PER_PLOT = 100
def redis_mem_set(butler,key,value):
    # Butler.memory is essentially set in redis
    butler.memory.set(key,pickle.dumps(value))



class AppDashboard(object):

  def __init__(self, db, ell):
    self.db = db
    self.ell = ell

  def basic_info(self,app,butler):
    """
    returns basic statistics like number of queries, participants, etc.
    """
    utils.debug_print("butler algo corona print2")
    utils.debug_print(butler.algorithms.get(pattern={'exp_uid':app.exp_uid}))

    experiment_dict = butler.experiment.get()
    # utils.debug_print("experiment_dict dasboard corona")
    # utils.debug_print(experiment_dict)
    alg_list = butler.experiment.get(key='args')['alg_list']
    # utils.debug_print("ALGO list app dasboard corona")
    # for algorithm in alg_list:
    #    utils.debug_print(algorithm)

    algo_dict = butler.algorithms.get(pattern={'exp_uid':app.exp_uid})
    utils.debug_print("algo_dict dasboard corona")
    utils.debug_print(algo_dict)

    #git_hash = rm.get_git_hash_for_exp_uid(exp_uid)
    git_hash = experiment_dict.get('git_hash','None')
    # labelled_list = butler.algorithms.get(key="labelled_list")
    # utils.debug_print("labelled_list app dasboard corona")
    # utils.debug_print(labelled_list)
    # start_date = utils.str2datetime(butler.admin.get(uid=app.exp_uid)['start_date'])
    start_date = experiment_dict.get('start_date','Unknown')+' UTC'

    # participant_uids = rm.get_participant_uids(exp_uid)
    participants = butler.participants.get(pattern={'exp_uid':app.exp_uid})
    num_participants = len(participants)

    queries = butler.queries.get(pattern={'exp_uid':app.exp_uid})
    num_queries = len(queries)

    return_dict = {'git_hash':git_hash,
                    'exp_start_data':start_date,
                    'num_participants':num_participants,
                    'num_queries':num_queries,
                    'meta':{'last_dashboard_update':'<1 minute ago'}}
    return return_dict

  def api_activity_histogram(self, app, butler):
    """
    Description: returns the data to plot all API activity (for all algorithms) in a histogram with respect to time for any task in {getQuery,processAnswer,predict}

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
    """
    queries = butler.queries.get(pattern={'exp_uid':app.exp_uid})
    #self.db.get_docs_with_filter(app_id+':queries',{'exp_uid':exp_uid})
    start_date = utils.str2datetime(butler.admin.get(uid=app.exp_uid)['start_date'])
    numerical_timestamps = [(utils.str2datetime(item['timestamp_query_generated'])-start_date).total_seconds()
                                for item in queries]
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

  def reset_redis(self, app, butler):

      bucket_id = os.environ.get("AWS_BUCKET_NAME")
      file_name_list = ['samples.csv', 'Labels.csv', 'studies.csv']
      csv_content_dict = s3.get_csv_content_dict(bucket_id, file_name_list)

      for filename, content in csv_content_dict.items():
          if filename is 'samples.csv':
              samples_df = pd.read_csv(io.BytesIO(content))
              # utils.debug_print("database_lib corona")
              # utils.debug_print(samples_df.head())
          elif filename is 'Labels.csv':
              labels_df = pd.read_csv(io.BytesIO(content))
              # utils.debug_print("database_lib corona")
              # utils.debug_print(labels_df.head())
          elif filename is 'studies.csv':
              study_df = pd.read_csv(io.BytesIO(content))
              # utils.debug_print("database_lib corona")
              # utils.debug_print(study_df.head())

      df_sort = labels_df.groupby(['dataset_type'])

      for dataset_type, df_cur in df_sort:
          if (dataset_type == constants.UNLABELLED_TAG):
              unlabelled_indices = df_cur['index'].tolist()
          elif (dataset_type == constants.TRAIN_TAG):
              train_indices = df_cur['index'].values
          elif (dataset_type == constants.TEST_TAG):
              test_indices = df_cur['index'].values

      batch_no = labels_df['batch_no'].max()
      if pd.isnull(batch_no):
          batch_no = 0

      butler.memory.set("batch_no", pickle.dumps(batch_no + 1))

      train_df = samples_df.loc[samples_df['index'].isin(train_indices)]
      train_df['label'] = labels_df.loc[labels_df['index'].isin(train_indices), 'label']

      test_df = samples_df.loc[samples_df['index'].isin(test_indices)]
      test_df['label'] = labels_df.loc[labels_df['index'].isin(test_indices), 'label']

      unlabelled_df = samples_df.loc[samples_df['index'].isin(unlabelled_indices)]
      X_unlabelled_str = lr.create_vector(unlabelled_df)
      N = 2
      bag_of_words = ["differentiated", "cell", "hela", "derived", "CL:0000057", "CL:0000115", "EFO:0000322","EFO:0000324", "EFO:0000313", "CL:0000034"]
      # create the transform
      vectorizer = TfidfVectorizer(ngram_range=(1, N + 1), decode_error='ignore')
      # tokenize and build vocab
      try:
          vectorizer.fit(bag_of_words)
      except Exception as e:
          utils.debug_print(e)

      X_train_str, y_train = lr.create_dict(train_df)
      X_test_str, y_test = lr.create_dict(test_df)

      # Encode y_train and y_test
      y_train = pd.Series(y_train)
      sample_dict = lr.get_encode_dict()
      y_train = y_train.replace(sample_dict).values

      y_test = pd.Series(y_test)
      y_test = y_test.replace(sample_dict).values

      # encode document
      try:
          X_train = vectorizer.transform(X_train_str)
      except Exception as e:
          utils.debug_print(e)

      try:
          X_test = vectorizer.transform(X_test_str)
      except Exception as e:
          utils.debug_print(e)

      try:
          X_unlabelled = vectorizer.transform(X_unlabelled_str)
      except Exception as e:
          utils.debug_print(e)

      study_id_list = unlabelled_df['sra_study_id'].tolist()

      for i, row in unlabelled_df.iterrows():
          utils.debug_print(str(row['index']))
          redis_mem_set(butler,str(row['index']), row)

      utils.debug_print("done setting unlabelled")

      lr_model = LogisticRegression(penalty='l1')
      lr_model.fit(X_train, y_train)
      y_pred = lr_model.predict(X_test)
      acc_init = accuracy_score(y_test, y_pred)
      utils.debug_print("acc in app dashboard")
      utils.debug_print(acc_init)
      largest_val = lr.get_largest_values(X_unlabelled, lr_model, unlabelled_indices, study_id_list, 5)
      sample_list = largest_val['index'].tolist()
      sample_probs = largest_val['prob'].tolist()
      lr_classes = lr.get_decode_list(lr_model.classes_)
      redis_mem_set(butler, 'lr_classes', lr_classes)

      utils.debug_print("sample_list init")
      utils.debug_print(sample_list)
      utils.debug_print("sample prob init")
      utils.debug_print(sample_probs)

      for i, row in study_df.iterrows():
          redis_mem_set(butler,row['sra_study_id'], row)

      #Making sure that the eariler batch hasnt been labelled before
      algo_list = butler.algorithms.get(pattern={'exp_uid': app.exp_uid})
      S_trial = {}
      # for cur_algo in algo_list:
      #     if cur_algo.get("alg_id") is "LogisticRegressionActive":
      #         S_trial = json.loads(cur_algo.get("S_trial"))
      #Remove hardcode
      cur_algo = algo_list[0]
      cur_algo["sample_probs"] = sample_probs
      cur_algo["sample_list"] = sample_list

      lr.redis_mem_set(butler, 'sample_probs', sample_probs)
      lr.redis_mem_set(butler, 'sample_list', sample_list)
      lr.redis_mem_set(butler, "study_id_list", study_id_list)
      # Set  data in mem
      # redis_mem_set(butler, "does_this_work", 5)
      lr.redis_mem_set(butler, "train_data", train_df)
      lr.redis_mem_set(butler, "bucket_id", bucket_id)
      lr.redis_mem_set(butler, "test_data", test_df)
      lr.redis_mem_set(butler, "unlabelled_data", unlabelled_df[['key_value', 'ontology_mapping']])
      lr.redis_mem_set(butler, "label_data", labels_df)
      lr.redis_mem_set(butler, "unlabelled_list", unlabelled_indices)
      lr.redis_mem_set(butler, "X_unlabelled", X_unlabelled)

      return {}

  def compute_duration_multiline_plot(self, app, butler, task):
    """
    Description: Returns multiline plot where there is a one-to-one mapping lines to
    algorithms and each line indicates the durations to complete the task (wrt to the api call)

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
    """

    alg_list = butler.experiment.get(key='args')['alg_list']
    x_min = numpy.float('inf')
    x_max = -numpy.float('inf')
    y_min = numpy.float('inf')
    y_max = -numpy.float('inf')
    list_of_alg_dicts = []

    for algorithm in alg_list:
      alg_label = algorithm['alg_label']
      list_of_log_dict = butler.ell.get_logs_with_filter(app.app_id+':ALG-DURATION',
                                                                            {'exp_uid':app.exp_uid,'alg_label':alg_label,'task':task})
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
      incr_inds = [ r*num_items/multiplier for r in range(multiplier)]
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


  def compute_duration_detailed_stacked_area_plot(self,app,butler,task,alg_label,detailedDB=False):
    """
    Description: Returns stacked area plot for a particular algorithm and task where the durations
    are broken down into compute,db_set,db_get (for cpu, database_set, database_get)

    Expected input:
      (string) task :  must be in {'getQuery','processAnswer','predict'}
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
    """
    list_of_log_dict = butler.ell.get_logs_with_filter(app.app_id+':ALG-DURATION',
                                                                          {'exp_uid':app.exp_uid,'alg_label':alg_label,'task':task})
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


  def response_time_histogram(self,app,butler,alg_label):
    """
    Description: returns the data to plot response time histogram of processAnswer for each algorithm

    Expected input:
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
    """
    list_of_query_dict = self.db.get_docs_with_filter(app.app_id+':queries',{'exp_uid':app.exp_uid,'alg_label':alg_label})
    t = []
    for item in list_of_query_dict:
      try:
        t.append(item['response_time'])
      except:
        pass

    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#FFFFFF'))
    ax.hist(t, bins=min(len(t), MAX_SAMPLES_PER_PLOT), range=(0,30),alpha=0.5,color='black')
    ax.set_xlim(0, 30)
    ax.set_axis_off()
    ax.set_xlabel('Durations (s)')
    ax.set_ylabel('Count')
    ax.set_title(alg_label + " - response time", size=14)
    plot_dict = mpld3.fig_to_dict(fig)
    plt.close()

    return plot_dict

  def network_delay_histogram(self, app, butler, alg_label):
    """
    Description: returns the data to network delay histogram of the time it takes to getQuery+processAnswer for each algorithm

    Expected input:
      (string) alg_label : must be a valid alg_label contained in alg_list list of dicts

    Expected output (in dict):
      (dict) MPLD3 plot dictionary
    """
    list_of_query_dict = self.db.get_docs_with_filter(app.app_id+':queries',{'exp_uid':app.exp_uid,'alg_label':alg_label})

    t = []
    for item in list_of_query_dict:
      try:
        t.append(item['network_delay'])
      except:
        pass

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

