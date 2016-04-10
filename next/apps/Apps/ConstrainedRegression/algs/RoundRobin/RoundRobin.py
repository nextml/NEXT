"""
RoundRobin app implements ConstrainedRegressionPrototype
author: Kevin Jamieson
last updated: 12/15/2015
"""

import numpy
import numpy.random
from next.apps.Apps.ConstrainedRegression.Prototype import ConstrainedRegressionPrototype

class RoundRobin(ConstrainedRegressionPrototype):

  def initExp(self,butler,n,R,failure_probability,params):
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='failure_probability',value=failure_probability)
    butler.algorithms.set(key='R',value=R)
    arm_key_value_dict = {}
    for i in range(n):
      arm_key_value_dict['Xsum_'+str(i)] = 0.
      arm_key_value_dict['X2sum_'+str(i)] = 0.
      arm_key_value_dict['T_'+str(i)] = 0.
    arm_key_value_dict.update({'total_pulls':0,'generated_queries_cnt':-1})
    butler.algorithms.increment_many(key_value_dict=arm_key_value_dict)

    return True


  def getQuery(self,butler,participant_dict,**kwargs):
    do_not_ask_hash = {key: True for key in participant_dict.get('do_not_ask_list',[])}

    n = butler.algorithms.get(key='n')
    cnt = butler.algorithms.increment(key='generated_queries_cnt',value=1)

    k=0
    while k<n and do_not_ask_hash.get(((cnt+k)%n),False):
      k+=1
    if k<n:
      index = (cnt+k)%n
    else:
      index = numpy.random.choice(n)

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


