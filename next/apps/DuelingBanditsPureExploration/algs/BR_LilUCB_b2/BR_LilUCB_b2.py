"""
BR_LilUCB app implements DuelingBanditsPureExplorationPrototype
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/11/2015

BR_LilUCB implements the lilUCB algorithm described in 
Jamieson, Malloy, Nowak, Bubeck, "lil' UCB : An Optimal Exploration Algorithm for Multi-Armed Bandits," COLT 2014
using the Borda reduction described in detail in
Jamieson et al "Sparse Borda Bandits," AISTATS 2015. 
"""

import numpy
import numpy.random
from next.apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype

class BR_LilUCB_b2(DuelingBanditsPureExplorationPrototype):

  def daemonProcess(self,resource,daemon_args_dict):
    return True
  
  def initExp(self,resource,n=0,failure_probability=0.05):
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.increment('total_pulls',0)
    for i in range(n):
      resource.increment('Xsum_'+str(i),0.)
      resource.increment('T_'+str(i),0)

    return True

  
  def getQuery(self,resource):
    beta = 0.0 # algorithm parameter

    n = resource.get('n')
    key_list = ['failure_probability']
    for i in range(n):
      key_list.append( 'Xsum_'+str(i) )
      key_list.append( 'T_'+str(i) )

    key_value_dict = resource.get_many(key_list)

    sumX = []
    T = []
    for i in range(n):
      sumX.append( key_value_dict['Xsum_'+str(i)] )
      T.append( key_value_dict['T_'+str(i)] )

    delta = key_value_dict['failure_probability']
    sigma_sq = .25

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
      return index,alt_index,index
    else:
      return alt_index,index,index


  def processAnswer(self,resource,index_left=0,index_right=0,index_painted=0,index_winner=0):
    alt_index = index_left
    if index_left==index_painted:
      alt_index = index_right

    reward = 0.
    if index_painted==index_winner:
      reward = 1.

    resource.increment_many({'Xsum_'+str(index_painted):reward,'T_'+str(index_painted):1,'total_pulls':1})
    
    return True

  def predict(self,resource):
    n = resource.get('n')

    key_list = []
    for i in range(n):
      key_list.append( 'Xsum_'+str(i) )
      key_list.append( 'T_'+str(i) )

    key_value_dict = resource.get_many(key_list)

    sumX = []
    T = []
    for i in range(n):
      sumX.append( key_value_dict['Xsum_'+str(i)] )
      T.append( key_value_dict['T_'+str(i)] )

    mu = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
      else:
        mu[i] = sumX[i] / T[i]

    prec = [ numpy.sqrt(1./max(1,t)) for t in T]
    
    return mu.tolist(),prec
    
