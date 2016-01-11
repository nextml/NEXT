"""
BR_Random app implements DuelingBanditsPureExplorationPrototype
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 11/4/2015

BR_Random implements random sampling  using the Borda reduction described in detail in
Jamieson et al "Sparse Borda Bandits," AISTATS 2015. 
"""

import numpy
import numpy.random
from next.apps.DuelingBanditsPureExploration.Prototype import DuelingBanditsPureExplorationPrototype

class BR_Random_b2(DuelingBanditsPureExplorationPrototype):

  def daemonProcess(self,resource,daemon_args_dict):
    return True
  
  def initExp(self,resource,n,failure_probability,params):
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.increment('total_pulls',0)
    for i in range(n):
      resource.increment('Xsum_'+str(i),0.)
      resource.increment('T_'+str(i),0)

    return True

  
  def getQuery(self,resource):
    n = resource.get('n')
    index = numpy.random.choice(n)
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


