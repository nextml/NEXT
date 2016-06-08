"""
BR_LilUCB app implements DuelingBanditsPureExplorationPrototype

BR_LilUCB implements the lilUCB algorithm described in 
Jamieson, Malloy, Nowak, Bubeck, "lil' UCB : An Optimal Exploration Algorithm for Multi-Armed Bandits," COLT 2014
using the Borda reduction described in detail in
Jamieson et al "Sparse Borda Bandits," AISTATS 2015. 
"""

import numpy
import numpy.random
# from next.apps.Apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype
import next.utils as utils

class BR_LilUCB:
  def initExp(self, butler, n, failure_probability, params):
    """
    This function is meant to set keys used later by the algorith implemented
    in this file.
    """
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='failure_probability', value=failure_probability)

    arm_key_value_dict = {}
    for i in range(n):
      arm_key_value_dict['Xsum_'+str(i)] = 0.
      arm_key_value_dict['T_'+str(i)] = 0.
    arm_key_value_dict.update({'total_pulls':0})
    butler.algorithms.increment_many(key_value_dict=arm_key_value_dict)

    return True
  
  def getQuery(self,butler,participant_dict,**kwargs):
    beta = 0.0 # algorithm parameter

    key_value_dict = butler.algorithms.get()
    n = key_value_dict['n']
    sumX = [key_value_dict['Xsum_'+str(i)] for i in range(n)]
    T = [key_value_dict['T_'+str(i)] for i in range(n)]

    delta = key_value_dict['failure_probability']
    sigma_sq = 0.25

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
        # UCB[i] = mu[i] + (1+beta)*numpy.sqrt( 2.0*sigma_sq*numpy.log( numpy.log(4*T[i])/delta ) / T[i] )
        UCB[i] = mu[i] + (1+beta)*numpy.sqrt( 2.0*sigma_sq*numpy.log( 4*T[i]*T[i]/delta ) / T[i] )

    if len(A)>0:
      index = numpy.random.choice(A)
    else:
      index = numpy.argmax(UCB)

    alt_index = numpy.random.choice(n)
    while alt_index==index:
      alt_index = numpy.random.choice(n)

    random_fork = numpy.random.choice(2)
    if random_fork==0:
      return [index,alt_index,index]
    else:
      return [alt_index,index,index]


  def processAnswer(self,butler, left_id=0, right_id=0, painted_id=0, winner_id=0):
    alt_index = left_id
    if left_id==painted_id:
      alt_index = right_id

    reward = 0.
    if painted_id==winner_id:
      reward = 1.

    butler.algorithms.increment_many(key_value_dict={'Xsum_'+str(painted_id):reward, 'T_'+str(painted_id):1., 'total_pulls':1})
    
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
    
  
 
