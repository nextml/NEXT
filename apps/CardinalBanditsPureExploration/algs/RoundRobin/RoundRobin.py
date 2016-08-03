"""
RoundRobin app implements CardinalBanditsPureExplorationPrototype
author: Kevin Jamieson
last updated: 12/15/2015
"""

import numpy
import numpy.random
from apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype

class RoundRobin(CardinalBanditsPureExplorationPrototype):

  def initExp(self,butler,n,R,failure_probability,params={}):
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='failure_probability',value=failure_probability)
    butler.algorithms.set(key='R',value=R)

    empty_list = numpy.zeros(n).tolist()
    butler.algorithms.set(key='Xsum',value=empty_list)
    butler.algorithms.set(key='X2sum',value=empty_list)
    butler.algorithms.set(key='T',value=empty_list)
    return True

  
  def getQuery(self,butler,participant_uid):
    participant_dict = butler.participants.get(uid=participant_uid)
    do_not_ask_hash = {key: True for key in participant_dict.get('do_not_ask_list',[])}
    
    kv_dict = butler.algorithms.increment_many(key_value_dict={'n':0,'generated_queries_cnt':1})
    n = kv_dict['n']
    cnt = kv_dict['generated_queries_cnt']-1

    k=0
    while k<n and do_not_ask_hash.get(((cnt+k)%n),False):
      k+=1
    if k<n:
      index = (cnt+k)%n
    else:
      index = numpy.random.choice(n)

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
    
    return mu.tolist(),prec.tolist(), T
    
  def update_priority_list(self,butler,args):
    S = butler.algorithms.get_and_delete(key='S')

    if S!=None:
      doc = butler.algorithms.get()

      Xsum = doc['Xsum']
      X2sum = doc['X2sum']
      T = doc['T']

      for q in S:
        Xsum[q[0]] += q[1]
        X2sum[q[0]] += q[1]*q[1]
        T[q[0]] += 1

      butler.algorithms.set_many(key_value_dict={'Xsum':Xsum,'X2sum':X2sum,'T':T})


