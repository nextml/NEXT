"""
BeatTheMean app implements DuelingBanditsPureExplorationPrototype
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/11/2015

BeatTheMean implements the Beat-The-Mean algorithm described in 
Yue and Joachims, "Beat the Mean Bandit," COLT 2011
originally designed for idenitfying the condorcet winner but works by removing non-Borda winners. 

We set gamma=1. and the fixed confidence setting of the algorithm. As done in their experiments, we 
remove the leading constant factor of '3' outfront equation (7) for their confidence bound.
"""

import numpy
import numpy.random
from next.apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype

class BeatTheMean(DuelingBanditsPureExplorationPrototype):

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
    running_sum_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.set('running_sum_vec',running_sum_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',0)
    resource.set('active_set',range(n))

    return True

  
  def getQuery(self,resource):
    n = resource.get('n')
    A = resource.get('active_set')

    if len(A)==0:
      painted_set = n
      alt_set = n
    elif len(A)==1:
      painted_set = A
      alt_set = n
    else:
      painted_set = A
      alt_set = A

    index = numpy.random.choice(painted_set)
    alt_index = numpy.random.choice(alt_set)
    while alt_index==index:
      alt_index = numpy.random.choice(alt_set)

    random_fork = numpy.random.choice(2)
    if random_fork==0:
      return index,alt_index,index
    else:
      return alt_index,index,index


  def processAnswer(self,resource,index_left=0,index_right=0,index_painted=0,index_winner=0):
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
    gamma = 1. # algorithm parameter

    n = resource.get('n')
    S = resource.get_list('S')
    A = resource.get('active_set')
    delta = resource.get('failure_probability')

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
      
    # compute statistics about old active-set
    mu = numpy.zeros(n)
    CB = numpy.zeros(n)
    sigma_sq = .25
    for i in range(n):
      if num_pulls_vec[i]==0:
        mu[i] = float('inf')
        CB[i] = float('inf')
      else:
        mu[i] = running_sum_vec[i] / num_pulls_vec[i]
        CB[i] = numpy.sqrt( 2.0*sigma_sq*numpy.log( 4*n*num_pulls_vec[i]*num_pulls_vec[i]/delta ) / num_pulls_vec[i] )

    # update active set
    i_hat = A[numpy.argmax(mu[A])]
    B = []
    for a in A:
      if CB[a]==float('inf') or CB[i_hat]==float('inf'):
        B.append(a)
      elif mu[i_hat]-CB[i_hat] < mu[a] + CB[a]:
        B.append(a)

    # update in-active-set statistics 
    running_sum_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()
    for q in S:
      index_winner = q[0]
      index_loser = q[1]
      index_painted = q[2]
      reward = (index_winner==index_painted)*1.0        
      if index_winner in B and index_loser in B:
        running_sum_vec[index_painted] += reward
        num_pulls_vec[index_painted] += 1

    resource.set('active_set',B)
    resource.set('running_sum_vec',running_sum_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',total_pulls)

