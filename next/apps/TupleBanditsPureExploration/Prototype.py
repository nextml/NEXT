"""
TupleBanditsPureExploration app of the Online Learning Library for Next.Discovery
author: Nick Glattard, n.glattard@gmail.com
last updated: 4/27/2015

TupleBanditsPureExplorationPrototype

This interface must be implemented by an app that solves the multi-armed tuple bandit, pure 
exploration problem. 
"""


class TupleBanditsPureExplorationPrototype(object):
  def __init__(self): 
    self.app_id = 'TupleBanditsPureExploration'

  def initExp(self,resource,n,k,failure_probability):
    """
    initialize the experiment 

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of arms
      (int) k : number of objects to display
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError


  def getQuery(self,resource):
    """
    A request to ask which k arms to duel next

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (comma separated): 
      (list) targets : list of target indices e.g. [ (int) target_index_1, ... , (int) target_index_k ]
    """
    return NotImplementedError

  
  def processAnswer(self,resource,targets,index_winner):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (list) targets : list of target indices e.g. [ (int) target_index_1, ... , (int) target_index_k ]
      (int) index_winner : index of arm must be in targets

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def predict(self,resource):
    """
    uses current model empirical estimates to forecast the ranking of the arms in order of likelhood of being the best from most to least likely

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (in dictionary): 
      (list int) arm_ranking : list of integers where the the ith arm at the jth index represents the belief that the ith arm is the jth most likely arm to be the ``best'' arm 
    """
    return NotImplementedError

  

