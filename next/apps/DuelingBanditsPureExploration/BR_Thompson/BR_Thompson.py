"""
BR_Thompson implements DuelingBanditsPureExplorationPrototype
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 5/20/2015

BR_Thompson implements the Thompson Sampling algorithm described in 
Chapelle and Li "An Empirical Evaluation of Thompson Sampling," NIPS 2012
using the Borda reduction described in detail in
Jamieson et al "Sparse Borda Bandits," AISTATS 2015. 
"""

import numpy
import numpy.random
from next.apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype

class BR_Thompson(DuelingBanditsPureExplorationPrototype):

  def daemonProcess(self,resource,daemon_args_dict):

    if 'task' in daemon_args_dict and 'args' in daemon_args_dict:
      task = daemon_args_dict['task']
      args = daemon_args_dict['args']
      if task == '__update_sufficient_statistics':
        self.__update_sufficient_statistics(resource,args)
    else:
      return False

    return True
  

  def initExp(self,resource,n=0,failure_probability=0.05):
    """
    initialize the experiment 

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of arms
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    running_sum_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()
    resource.set('n',n)
    resource.set('running_sum_vec',running_sum_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',0)

    return True

  
  def getQuery(self,resource):
    """
    A request to ask which two arms to duel next

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (comma separated): 
      (int) index_left : index of arm must be in {0,1,2,...,n-1}
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_left
      (int) index_painted : index of arm must be in {0,1,2,...,n-1}
    """
    alpha = 2

    hits = resource.get('running_sum_vec')
    trials = resource.get('num_pulls_vec')
    n = len(trials)

    theta = numpy.zeros(n)
    for i in range(n):
      theta[i] = numpy.random.beta(max(1,(1+hits[i])/alpha),max(1,(1+trials[i]-hits[i])/alpha))

    index = numpy.argmax(theta)

    alt_index = numpy.random.choice(n)
    while alt_index==index:
      alt_index = numpy.random.choice(n)

    random_fork = numpy.random.choice(2)
    if random_fork==0:
      return index,alt_index,index
    else:
      return alt_index,index,index


  def processAnswer(self,resource,index_left=0,index_right=0,index_painted=0,index_winner=0):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) index_left : index of arm must be in {0,1,2,...,n-1}
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_left
      (int) index_painted : index of arm must be in {0,1,2,...,n-1}
      (int) index_winner : index of arm must be {index_left,index_right}

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """

    alt_index = index_left
    if index_left==index_painted:
      alt_index = index_right

    if index_painted==index_winner:
      index_loser = alt_index
    else:
      index_loser = index_painted

    q = [index_winner,index_loser,index_painted]
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
    sumX = resource.get('running_sum_vec')
    T = resource.get('num_pulls_vec')

    mu = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
      else:
        mu[i] = sumX[i] / T[i]

    prec = [ numpy.sqrt(1./max(1,t)) for t in T]
    
    return mu.tolist(),prec

  def __update_sufficient_statistics(self,resource,args):

    n = resource.get('n')
    S = resource.get_list('S')

    running_sum_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()

    for q in S:
      index_winner = q[0]
      index_loser = q[1]
      index_painted = q[2]

      if index_winner==index_painted:
        running_sum_vec[index_painted] += 1
      num_pulls_vec[index_painted] += 1

    total_pulls = len(S)

    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('running_sum_vec',running_sum_vec)
    resource.set('total_pulls',total_pulls)

