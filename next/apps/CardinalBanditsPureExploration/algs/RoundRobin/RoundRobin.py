"""
RoundRobin app implements CardinalBanditsPureExplorationPrototype
author: Kevin Jamieson
last updated: 12/15/2015
"""

import numpy
import numpy.random
from next.apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype

class RoundRobin(CardinalBanditsPureExplorationPrototype):

  def initExp(self,resource,n,R,failure_probability,params):
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.set('R',R)
    resource.increment('generated_queries_cnt',-1)
    resource.increment('total_pulls',0)
    for i in range(n):
      resource.increment('Xsum_'+str(i),0.)
      resource.increment('X2sum_'+str(i),0.)
      resource.increment('T_'+str(i),0)

    return True

  
  def getQuery(self,resource,do_not_ask_list):
    n = resource.get('n')
    cnt = resource.increment('generated_queries_cnt',1)

    index = cnt % n

    return index

  def processAnswer(self,resource,target_index,target_reward): 
    resource.increment_many({'Xsum_'+str(target_index):target_reward,'X2sum_'+str(target_index):target_reward*target_reward,'T_'+str(target_index):1,'total_pulls':1})
    
    return True

  def predict(self,resource):
    n = resource.get('n')

    key_list = ['R']
    for i in range(n):
      key_list.append( 'Xsum_'+str(i) )
      key_list.append( 'X2sum_'+str(i) )
      key_list.append( 'T_'+str(i) )

    key_value_dict = resource.get_many(key_list)

    R = key_value_dict['R']
    
    sumX = []
    sumX2 = []
    T = []
    for i in range(n):
      sumX.append( key_value_dict['Xsum_'+str(i)] )
      sumX2.append( key_value_dict['X2sum_'+str(i)] )
      T.append( key_value_dict['T_'+str(i)] )

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
        prec[i] = numpy.sqrt( float( max(R*R,sumX2[i] - T[i]*mu[i]*mu[i]) ) / ( T[i] - 1. ) / T[i] )
    
    return mu.tolist(),prec.tolist()



