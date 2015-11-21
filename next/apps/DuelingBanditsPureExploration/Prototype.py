"""
DuelingBanditsPureExploration app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/11/2015

DuelingBanditsPureExplorationPrototype

This interface must be implemented by an app that solves the multi-armed dueling bandit, pure 
exploration problem for the Borda rule. 
"""


class DuelingBanditsPureExplorationPrototype(object):
  def __init__(self): 
    self.app_id = 'DuelingBanditsPureExploration'

  def initExp(self,resource,n=0,failure_probability=0.05):
    """
    initialize the experiment 

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of arms
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError


  def getQuery(self,resource):
    """
    A request to ask which two arms to duel next

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (in dictionary): 
      (int) index_left : index of arm must be in {0,1,2,...,n-1}
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_left
      (int) index_painted : index of arm must be in {0,1,2,...,n-1}
    """
    return NotImplementedError

  
  def processAnswer(self,resource,index_left=0,index_right=0,index_winner=0):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (int) index_left : index of arm must be in {0,1,2,...,n-1}
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_left
      (int) index_painted : index of arm must be in {0,1,2,...,n-1}
      (int) index_winner : index of arm must be {index_left,index_right}

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def predict(self,resource):
    """
    uses current model empirical estimates to forecast which index is the winner

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (in dictionary): 
      (int) predicted_index : must be in {0,1,2,...,n-1}
    """
    return NotImplementedError
