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
  
  def initExp(self,resource,n=0,failure_probability=0.05):
    """
    initialize the experiment 

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of arms
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.increment('total_pulls',0)
    for i in range(n):
      resource.increment('Xsum_'+str(i),0.)
      resource.increment('T_'+str(i),0)

    return True

  
  def getQuery(self,resource):
    """
    A request to ask which two arms to duel next

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (comma separated): 
      (int) index_left : index of arm must be in {0,1,2,...,n-1}
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_left
      (int) index_painted : index of arm must be in {0,1,2,...,n-1}
    """

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
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) index_left : index of arm must be in {0,1,2,...,n-1}
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_left
      (int) index_painted : index of arm must be in {0,1,2,...,n-1}
      (int) index_winner : index of arm must be {index_left,index_right}

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """

    alt_index = index_left
    if index_left==index_painted:
      alt_index = index_right

    reward = 0.
    if index_painted==index_winner:
      reward = 1.

    resource.increment_many({'Xsum_'+str(index_painted):reward,'T_'+str(index_painted):1,'total_pulls':1})
    
    return True

  def predict(self,resource):
    """
    uses current model empirical estimates to forecast the ranking of the arms in order of likelhood of being the best from most to least likely

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (in dictionary): 
      (list int) arm_ranking : list of integers where the the ith arm at the jth index represents the belief that the ith arm is the jth most likely arm to be the ``best'' arm 
    """
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


