"""
LilUCB app implements CardinalBanditsPureExplorationPrototype
author: Kevin Jamieson
last updated: 11/13/2015
"""

import numpy
import numpy.random
from next.apps.Apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype

class LilUCB(CardinalBanditsPureExplorationPrototype):

  def initExp(self,butler,n,R,failure_probability,params):
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='delta',value=failure_probability)
    butler.algorithms.set(key='R',value=R)

    empty_list = numpy.zeros(n).tolist()
    butler.algorithms.set(key='Xsum',value=empty_list)
    butler.algorithms.set(key='X2sum',value=empty_list)
    butler.algorithms.set(key='T',value=empty_list)

    priority_list = numpy.random.permutation(n).tolist()
    butler.algorithms.set(key='priority_list',value=priority_list)

    return True

  
  def getQuery(self,butler,participant_dict,**kwargs):
    do_not_ask_hash = {key: True for key in participant_dict.get('do_not_ask_list',[])}

    kv_dict = butler.algorithms.increment_many(key_value_dict={'priority_list':0,'priority_list_cnt':1}) 
    priority_list = kv_dict['priority_list']
    priority_list_cnt = kv_dict['priority_list_cnt']

    k = (priority_list_cnt-1) % len(priority_list)
    while k<len(priority_list) and do_not_ask_hash.get(priority_list[k],False):
      k+=1
    if k==len(priority_list):
      index = numpy.random.choice(priority_list)
    else:
      index = priority_list[k]

    return index

  def processAnswer(self,butler,target_id,target_reward): 
    butler.algorithms.append(key='S',value=(target_id,target_reward))

    if numpy.random.rand()<.1: # occurs about 1/10 of trials
      butler.job('update_priority_list', {},time_limit=5)

    return True

  def getModel(self,butler):
    key_value_dict = butler.algorithms.get()
    R = key_value_dict['R']
    n = key_value_dict['n']
    sumX = key_value_dict['Xsum']
    sumX2 = key_value_dict['X2sum']
    T = key_value_dict['T']

    mu = numpy.zeros(n)
    prec = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
        prec[i] = -1
      elif T[i]==1:
        mu[i] = float(sumX[i]) / T[i]
        prec[i] = R
      else:
        mu[i] = float(sumX[i]) / T[i]
        prec[i] = numpy.sqrt( float( max(1.,sumX2[i] - T[i]*mu[i]*mu[i]) ) / ( T[i] - 1. ) / T[i] )
    
    return mu.tolist(),prec.tolist()

  def update_priority_list(self,butler,args):
    S = butler.algorithms.get_and_delete(key='S')

    if S!=None:
      doc = butler.algorithms.get()

      R = doc['R']
      delta = doc['delta']
      n = doc['n']
      Xsum = doc['Xsum']
      X2sum = doc['X2sum']
      T = doc['T']

      for q in S:
        Xsum[q[0]] += q[1]
        X2sum[q[0]] += q[1]*q[1]
        T[q[0]] += 1

      mu = numpy.zeros(n)
      UCB = numpy.zeros(n)
      for i in range(n):
        if T[i]==0:
          mu[i] = float('inf')
          UCB[i] = float('inf')
        else:
          mu[i] = Xsum[i] / T[i]
          UCB[i] = mu[i] + numpy.sqrt( 2.0*R*R*numpy.log( 4*T[i]*T[i]/delta ) / T[i] )

      # sort by -UCB first then break ties randomly
      priority_list = numpy.lexsort((numpy.random.randn(n),-UCB)).tolist() 

      butler.algorithms.set_many(key_value_dict={'priority_list':priority_list,'priority_list_cnt':0,'Xsum':Xsum,'X2sum':X2sum,'T':T})


