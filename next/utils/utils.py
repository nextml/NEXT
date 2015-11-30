"""
Utilities for using the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 2/17/2015

######################################
Serves as a library of utilities for all the adaptive and online learning applications on next.dicovery.

There exist a few distinct sections:
- Learning Library Utilties, utilities for app and alg including lists of implemnted algs and how to get alg objects
- Namespace Utilities, utilities for interacting with namespaces used in the database
- Time Utilities, utilities dealing with timing code and timestamps 

Usage: ::\n
  import next.utils as utils

  app_id_list = utils.supportedApps()
  for app_id in app_id_list:
    print app_id
    alg_id_list = utils.supportedAlgs(app_id)
    for alg_id in alg_id_list:
      print "\t-> "+alg_id

which outputs: ::\n
  StochasticBanditsPureExploration
    -> LilUCB
    -> LUCB
    -> SuccElim
  DuelingBanditsPureExploration
    -> BR_LilUCB
  StochasticLinearBanditsExploreExploit
    -> OFUL
    -> UE
  PoolBasedTripletMDS
    -> UncertaintySampling
    -> RandomSampling
"""

"""
Learning Library Utilties
#########################
"""
def get_supported_apps():
  """
  Returns a list of strings correspdoning to the app_id's that are fully operational in the learning library.

  Usage: ::\n
    app_id_list = utils.get_supported_apps()
    print app_id_list
    >>> ['StochasticBanditsPureExploration', 'DuelingBanditsPureExploration', 'StochasticLinearBanditsExploreExploit', 'PoolBasedTripletMDS']
  """
  next_path = 'next.apps'
  app_module = __import__(next_path,fromlist=[''])
  return app_module.implemented_apps

def get_app_about(app_id):
  """
  Returns a string with a high-level description of the app

  Usage: ::\n
    about = utils.get_default_alg_list('PoolBasedTripletMDS')
    print about
  """
  app_id = str(app_id) # sometimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_about()

def get_app_info_object(app_id):
  """
  Returns a string with a high-level description of the app

  Usage: ::\n
    about = utils.get_default_alg_list('PoolBasedTripletMDS')
    print about
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_info_object()

def get_app_default_instructions(app_id):
  """
  Returns a string with default instructions for the app (can be overwritten on initExp)

  Usage: ::\n
    about = utils.get_app_default_instructions('PoolBasedTripletMDS')
    print about
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_default_instructions()

def get_app_default_debrief(app_id):
  """
  Returns a string with default debrief for the app (can be overwritten on initExp)

  Usage: ::\n
    about = utils.get_default_debrief('PoolBasedTripletMDS')
    print about
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_default_debrief()

def get_app_default_num_tries(app_id):
  """
  Returns an int with default num_tries for the app (can be overwritten on initExp)

  Usage: ::\n
    about = utils.get_app_default_num_tries('PoolBasedTripletMDS')
    print about
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_default_num_tries()

def get_app(app_id):
  """ 
  Returns an object correspoding to the app_id that contains methods like initExp,getQuery,etc.

  Usage: ::\n
    app = utils.get_app(app_id)
    print app
    >>> <next.apps.StochasticBanditsPureExploration.StochasticBanditsPureExploration.StochasticBanditsPureExploration object at 0x103c9dcd0>
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  app_class = getattr(app_module,app_id)
  return app_class()

def get_app_alg(app_id,alg_id):
  """
  Returns an object correspoding to the alg_id that contains methods like initExp,getQuery,etc.
  Note that each algorithm (with an alg_id) is a child of an app (with an app_id), hence the app_id input

  Usage: ::\n
    alg = utils.get_app_alg(app_id,alg_id) 
    print alg
    >>> <next.apps.PoolBasedTripletMDS.RandomSampling.RandomSampling.RandomSampling object at 0x103cb7e10>
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  alg_id = str(alg_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'+app_id+'.algs.'
  alg_module = __import__(next_path+alg_id,fromlist=[''])
  alg_class = getattr(alg_module,alg_id)
  return alg_class()

def get_app_supported_algs(app_id):
  """
  Returns a list of strings correspdoning to the alg_id's that are fully operational in the learning library for the given app_id.

  Usage: ::\n
    alg_id_list = utils.get_app_supported_algs('StochasticBanditsPureExploration')
    print alg_id_list
    >>> ['LilUCB', 'LUCB', 'SuccElim']
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_implemented_algs()

def get_app_supported_stats(app_id):
  """
  Returns a list of dicts describing the stats available for the app and what are the necessary inputs

  Usage: ::\n
    stat_list = utils.get_app_supported_stats('PoolBasedTripletMDS')
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'+app_id+'.'
  dashboard_module = __import__(next_path+'Dashboard',fromlist=[''])
  dashboard_class = getattr(dashboard_module,app_id+'Dashboard')
  dashboard = dashboard_class()
  return dashboard.get_app_supported_stats()


def get_app_default_alg_list(app_id):
  """
  The NEXT system was designed with evaluation in mind meaning that users would upload their own algorithms or 
  compare exsiting algorithms on their use cases. However, a number of users just want to use NEXT as a system
  to adaptively collect data or just organized their data collection task. For this purpose, we have a set of defaults 
  for the algorithms and input parameters.

  This script is primarily used for the internals of the system but may be of interest to those wondering what an example alg_list looks like.
  
  Usage: ::\n
    alg_list = utils.get_app_default_alg_list('PoolBasedTripletMDS')
    print json.dumps(alg_list,indent=2)
    [
      {
        "alg_label": "Test", 
        "alg_id": "RandomSampling", 
        "proportion": 0.1, 
        "test_alg_label": "Test", 
        "params": {}
      }, 
      {
        "alg_label": "Random", 
        "alg_id": "RandomSampling", 
        "proportion": 0.45, 
        "test_alg_label": "Test", 
        "params": {}
      }, 
      {
        "alg_label": "Uncertainty Sampling", 
        "alg_id": "UncertaintySampling", 
        "proportion": 0.45, 
        "test_alg_label": "Test", 
        "params": {}
      }
    ]
  """
  app_id = str(app_id) # soemtimes input is unicode formatted which causes error
  next_path = 'next.apps.'
  app_module = __import__(next_path+app_id,fromlist=[''])
  return app_module.get_default_alg_list()




"""
Namespace Utilties
#########################
"""
def getDocUID(exp_uid,alg_uid=None):
  """
  Each instance of an app (with an (app_id,exp_uid) pair) and an algorithm (with an (app_id,exp_uid,alg_id,alg_uid) tuple)
  gets its own namespace. This method defines that namespace given the exp_uid, or (exp_uid,alg_uid)

  Usage::\n
    print utils.getDocUID(exp_uid)
    >>> 'eee9d58c61d580029113ba593446d23a'

    print utils.getDocUID(exp_uid,alg_uid)
    >>> 'eee9d58c61d580029113ba593446d23a-f081d374abac6c009f5a74877f8b9f3c'
  """
  if alg_uid==None:
    return exp_uid
  else:
    return exp_uid + "-" + alg_uid

import os
def getNewUID():
  """
  Returns length 32 string of random hex that is generated from machine state - good enough for cryptography
  Probability of collision is 1 in 340282366920938463463374607431768211456 

  Used for unique identifiers all over the system
  """
  uid = os.urandom(16).encode('hex')
  return uid



"""
Time Utilities
#########################
"""
from datetime import datetime
def datetimeNow(format='datetime'):
  """
  Returns the current datetime in the format used throughout the system. 
  For consistency, one should ALWAYS call this method, do not make your own call to datetime.

  Usage: ::\n
    utils.datetimeNow()
    >>> datetime.datetime(2015, 2, 17, 11, 5, 56, 27822)
  """
  date = datetime.now()
  if format=='string':
    return datetime2str(date)
  else:
    return date

def datetime2filename(obj_datetime):
  """
  Converts a datetime string into a datetime object in the system.
  For consistency, one should never use their own method of converting to string, always use this method. 
  
  Usage: ::\n
    date = utils.datetimeNow()
    date_str = utils.datetime2str(date)
    print date_str
    >>> '2015-02-17 11:11:07.489925'
  """
  return obj_datetime.strftime("%Y-%m-%d_%H:%M:%S")

def datetime2str(obj_datetime):
  """
  Converts a datetime string into a datetime object in the system.
  For consistency, one should never use their own method of converting to string, always use this method. 
  
  Usage: ::\n
    date = utils.datetimeNow()
    date_str = utils.datetime2str(date)
    print date_str
    >>> '2015-02-17 11:11:07.489925'
  """
  return str(obj_datetime)

def str2datetime(str_time):
  """
  Converts a datetime object into the string format used in the system.
  For consistency, one should never use their own method of converting to string, always use this method. 
  
  Usage: ::\n
    date = utils.datetimeNow()
    date_str = utils.datetime2str(date)
    utils.str2datetime(date_str)
  """
  try:
    return datetime.strptime(str_time,'%Y-%m-%d %H:%M:%S.%f')
  except:
    return datetime.strptime(str_time,'%Y-%m-%d %H:%M:%S')

import time
def timeit(f):
  """ 
  Utility used to time the duration of code execution. This script can be composed with any other script.

  Usage::\n
    def f(n): 
      return n**n  

    def g(n): 
      return n,n**n 

    answer0,dt = timeit(f)(3)
    answer1,answer2,dt = timeit(g)(3)
  """
  def timed(*args, **kw):
    ts = time.time()
    result = f(*args, **kw)
    te = time.time()
    if type(result)==tuple:
      return result + ((te-ts),)
    else:
      return result,(te-ts)
  return timed


    

    
