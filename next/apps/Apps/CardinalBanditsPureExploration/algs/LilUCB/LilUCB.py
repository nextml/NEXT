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
    butler.algorithms.set(key='failure_probability',value=failure_probability)
    butler.algorithms.set(key='R',value=R)
    butler.algorithms.increment(key='generated_queries_cnt',value=-1)
    butler.algorithms.increment(key='total_pulls',value=0)
    for i in range(n):
      butler.algorithms.increment(key='Xsum_'+str(i),value=0.)
      butler.algorithms.increment(key='X2sum_'+str(i),value=0.)
      butler.algorithms.increment(key='T_'+str(i),value=0)

    return True

  
  def getQuery(self,butler,do_not_ask_list):
    do_not_ask_hash = {key: True for key in do_not_ask_list}

    key_value_dict = butler.algorithms.get()
    n = key_value_dict['n']
    sumX = [key_value_dict['Xsum_'+str(i)] for i in range(n)]
    T = [key_value_dict['T_'+str(i)] for i in range(n)]

    R = key_value_dict['R']
    delta = key_value_dict['failure_probability']

    T = numpy.array(T)
    mu = numpy.zeros(n)
    UCB = numpy.zeros(n)
    A = []
    for i in range(n):
      if T[i]==0:
        mu[i] = float('inf')
        UCB[i] = float('inf')
        A.append(i)
      else:
        mu[i] = sumX[i] / T[i]
        UCB[i] = mu[i] + numpy.sqrt( 2.0*R*R*numpy.log( 4*T[i]*T[i]/delta ) / T[i] )

    if len(A)>0:
      priority_list = numpy.random.permutation(A)
    else:
      priority_list = numpy.argsort(-UCB)
    
    k = 0
    while k<len(priority_list) and do_not_ask_hash.get(priority_list[k],False): 
      k+=1
    if k==len(priority_list):
      index = numpy.random.randint(n)
    else:
      index = priority_list[k]

    return index

  def processAnswer(self,butler,target_id,target_reward): 
    butler.algorithms.increment_many(key_value_dict={'Xsum_'+str(target_id):target_reward,'X2sum_'+str(target_id):target_reward*target_reward,'T_'+str(target_id):1,'total_pulls':1})
    
    return True

  def getModel(self,butler):
    key_value_dict = butler.algorithms.get()
    n = key_value_dict['n']
    sumX = [key_value_dict['Xsum_'+str(i)] for i in range(n)]
    T = [key_value_dict['T_'+str(i)] for i in range(n)]

    mu = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
      else:
        mu[i] = sumX[i] / T[i]

    prec = [numpy.sqrt(1.0/max(1,t)) for t in T]
    
    return mu.tolist(),prec


