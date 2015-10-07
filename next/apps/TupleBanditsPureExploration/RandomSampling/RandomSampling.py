"""
RandomSampling app implements TupleBanditsPureExplorationPrototype
author: Nick Glattard, n.glattard@gmail.com
last updated: 4/27/2015
"""

import numpy
import numpy.random
from next.apps.TupleBanditsPureExploration.Prototype import TupleBanditsPureExplorationPrototype

class RandomSampling(TupleBanditsPureExplorationPrototype):

  def daemonProcess(self,resource,daemon_args_dict):

    if 'task' in daemon_args_dict and 'args' in daemon_args_dict:
      task = daemon_args_dict['task']
      args = daemon_args_dict['args']
      if task == '__update_sufficient_statistics':
        self.__update_sufficient_statistics(resource,args)
    else:
      return False

    return True
  
  def initExp(self,resource,n=0,k=0,failure_probability=0.05):
    """
    initialize the experiment 

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of arms
      (int) k : number of objects to display
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    running_wins_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()

    resource.set('n',n)
    resource.set('k',k)
    resource.set('failure_probability',failure_probability)
    resource.set('running_wins_vec',running_wins_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',0)

    return True

  
  def getQuery(self,resource):
    """
    A request to ask which k arms to duel next

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (comma separated): 
      (list) targets : list of target indices e.g. [ (int) target_index_1, ... , (int) target_index_k ]
    """
    # get parameters of experiment
    n = resource.get('n')
    k = resource.get('k')

    # create list to populate with target indices
    targets = numpy.random.choice(n,k,replace=False).tolist()

    return targets

  def processAnswer(self,resource,targets,index_winner=0):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (list) targets : list of target indices e.g. [ (int) target_index_1, ... , (int) target_index_k ]
      (int) index_winner : index of arm must be in targets

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    
    # q is the list of targets with the index winner at index 0
    q = targets
    q.remove(index_winner)
    q.insert(0,index_winner)
    resource.append_list('S',q)

    daemon_args_dict = {'task':'__update_sufficient_statistics','args':{}}
    resource.daemonProcess(daemon_args_dict,time_limit=1)
    
    return True

  def predict(self,resource):
    """
    uses current model empirical estimates to forecast the ranking of the arms in order of likelhood of being the best from most to least likely

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (in dictionary): 
      (list int) arm_ranking : list of integers where the the ith arm at the jth index represents the belief that the ith arm is the jth most likely arm to be the ``best'' arm 
    """
    n = resource.get('n')
    T = resource.get('num_pulls_vec')
    wins_vec = resource.get('running_wins_vec')

    mu = [ 1.0*wins_vec[i]/T[i] for i in range(n)]
    prec = [ numpy.sqrt(1.0/t) for t in T]
    
    return mu,prec
    
  def getStats(self,resource):
    """
    reports statistics on the experiment model or process

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      
    Expected output (comma separated): 
      (list(list(int))) S : list of recorded query lists with first index as the winner
    """
    S = resource.get_list('S')

    stats = {}
    stats['S'] = S

    return stats

  def __update_sufficient_statistics(self,resource,args):

    n = resource.get('n')
    S = resource.get_list('S')

    running_wins_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()

    # loop through query report answers
    for q in S:
      index_winner = q[0]

      running_wins_vec[index_winner] += 1
      for idx in q:
        num_pulls_vec[idx] += 1

    total_pulls = len(S)

    resource.set('running_wins_vec',running_wins_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',total_pulls)

