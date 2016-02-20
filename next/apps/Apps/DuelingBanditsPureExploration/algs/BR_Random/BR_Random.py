"""
BR_Random app implements DuelingBanditsPureExplorationPrototype
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 11/4/2015

BR_Random implements random sampling  using the Borda reduction described in detail in
Jamieson et al "Sparse Borda Bandits," AISTATS 2015. 
"""

import numpy
import numpy.random
from next.apps.Apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype

class BR_Random(DuelingBanditsPureExplorationPrototype):

  def initExp(self, butler, n, failure_probability, params):
    """
    This function is meant to set keys used later by the algorith implemented
    in this file.
    """
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='failure_probability', value=failure_probability)

    butler.algorithms.set(key='total_pulls', value=0)
    for i in range(n):
      butler.algorithms.set(key='Xsum_'+str(i), value=0.0)
      butler.algorithms.set(key='T_'+str(i), value=0.0)

    return True


  def getQuery(self,butler, do_not_ask_list):
    n = butler.algorithms.get(key='n')

    index = numpy.random.choice(n)
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


