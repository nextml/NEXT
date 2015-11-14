"""
CardinalBanditsPureExploration app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson
last updated: 11/13/2015

CardinalBanditsPureExplorationPrototype

This interface must be implemented by an app that solves the multi-armed bandit, pure 
exploration problem. 
"""


class CardinalBanditsPureExplorationPrototype(object):
  def __init__(self): 
    self.app_id = 'CardinalBanditsPureExploration'

  def initExp(self,resource,n,R,failure_probability):
    """
    initialize the experiment 

    Expected input:
      (next.database.ResourceClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of arms
      (float) R : sub-Gaussian parameter, e.g. E[exp(t*X)]<=exp(t^2 R^2/2), defaults to R=0.5 (satisfies X \in [0,1])
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def getQuery(self,resource):
    """
    A request to ask which index/arm to pull

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output (comma separated): 
      (int) target_index : idnex of arm to pull (in 0,n-1)
    """
    return NotImplementedError
  
  def processAnswer(self,resource,target_index,target_reward):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) target_index : index of arm pulled
      (int) target_reward : reward of arm pulled

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def predict(self,resource):
    """
    uses current model to return empirical estimates with uncertainties

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output: 
      (list float) mu : list of floats representing the emprirical means
      (list float) prec : list of floats representing the precision values (standard deviation)
    """
    return NotImplementedError
    