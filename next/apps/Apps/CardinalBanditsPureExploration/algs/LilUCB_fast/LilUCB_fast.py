"""
LilUCB_fast app implements CardinalBanditsPureExplorationPrototype
author: Kevin Jamieson
last updated: 11/13/2015
"""

import numpy
import numpy.random
from next.apps.Apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype

class LilUCB_fast(CardinalBanditsPureExplorationPrototype):

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

    butler.algorithms.increment(key='total_pulls',value=0)

    return True

  
  def getQuery(self,butler,participant_dict,**kwargs):
    do_not_ask_hash = {key: True for key in participant_dict.get('do_not_ask_list',[])}

    priority_list = butler.algorithms.get(key='priority_list')
    
    k = 0
    while k<len(priority_list) and do_not_ask_hash.get(priority_list[k],False): 
      k+=1
    if k==len(priority_list):
      index = numpy.random.randint(n)
    else:
      index = priority_list[k]

    return index

  def processAnswer(self,butler,target_id,target_reward): 
    butler.algorithms.append(key='S',value=(target_id,target_reward))
    total_pulls = butler.algorithms.increment(key='total_pulls',value=1)

    if total_pulls % 10 == 0:
      butler.job('update_priority_list', {},time_limit=5)

    return True

  def getModel(self,butler):
    key_value_dict = butler.algorithms.get()
    n = key_value_dict['n']
    Xsum = key_value_dict['Xsum']
    T = key_value_dict['T']

    mu = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
      else:
        mu[i] = Xsum[i] / T[i]

    prec = [numpy.sqrt(1.0/max(1,t)) for t in T]
    
    return mu.tolist(),prec

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

      priority_list = numpy.argsort(-UCB).tolist()

      butler.algorithms.set_many(key_value_dict={'priority_list':priority_list,'Xsum':Xsum,'X2sum':X2sum,'T':T})



