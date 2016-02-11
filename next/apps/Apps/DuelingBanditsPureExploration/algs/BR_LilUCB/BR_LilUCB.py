"""
BR_LilUCB app implements DuelingBanditsPureExplorationPrototype

BR_LilUCB implements the lilUCB algorithm described in 
Jamieson, Malloy, Nowak, Bubeck, "lil' UCB : An Optimal Exploration Algorithm for Multi-Armed Bandits," COLT 2014
using the Borda reduction described in detail in
Jamieson et al "Sparse Borda Bandits," AISTATS 2015. 
"""

import numpy
import numpy.random
#from next.apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype

#class BR_LilUCB(DuelingBanditsPureExplorationPrototype):
class BR_LilUCB:

  def getModel(self, butler, **kwargs):
    return butler.algorithms.get(key='num_reported_answers')
  
  def initExp(self, butler, n, failure_probability, params, **kwargs):
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='failure_probability', value=failure_probability)

    butler.algorithms.set(key='total_pulls', value=0)
    for i in range(n):
      butler.algorithms.set(key='Xsum_'+str(i), value=0.0)
      butler.algorithms.set(key='T_'+str(i), value=0.0)

    return True
  
  def getQuery(self, butler):
    beta = 0.0 # algorithm parameter

    n = butler.algorithms.get(key='n')
    key_value_dict = butler.algorithms.get()

    sumX = [key_value_dict[key] for key in key_value_dict if 'Xsum_' in key]
    T = [key_value_dict[key] for key in key_value_dict if 'T_' in key]

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


  def processAnswer(self,butler,index_left=0,index_right=0,index_painted=0,index_winner=0):
    alt_index = index_left
    if index_left==index_painted:
      alt_index = index_right

    reward = 0.
    if index_painted==index_winner:
      reward = 1.

    butler.algorithms.increment(key='Xum_'+str(index_painted), value=reward)
    butler.algorithms.increment(key=['T_'+str(index_painted), 'total_pulls'])
    
    return True

  def getModel(self,butler):
    n = butler.algorithms.get(key='n')

    key_list = ['Xsum_'+str(i) for i in range(n)]
    key_list += ['T_'+str(i) for i in range(n)]

    key_value_dict = butler.algorithms.get(key=key_list)

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
    
