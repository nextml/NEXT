"""
PoolBasedBinaryClassification app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 4/8/2015

PoolBasedBinaryClassificationPrototype

"""


class PoolBasedBinaryClassificationPrototype(object):
  def __init__(self): 
    self.app_id = 'PoolBasedBinaryClassification'

  def initExp(self,resource,n,d,failure_probability,params):
    """
    initialize the experiment 

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of objects
      (int) d : desired dimension
      (float) failure_probability : confidence
      (dict) params : algorithm-specific parameters (if none provided in alg_list of init experiment, params=None)

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError


  def getQuery(self,resource):
    """
    A request to ask which triplet to ask next

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output: 
      (int) index_center : index of arm must be in {0,1,2,...,n-1}
      (int) index_left : index of arm must be in {0,1,2,...,n-1} - index_center
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_center - index_left
    """
    return NotImplementedError

  
  def processAnswer(self,db,index=0,reward=0.5):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (int) index_center : index of center object
      (int) index_left : index of left object
      (int) index_right : index of right object
      (int) index_winner : index of winner object, index_winner in {index_left,index_right}

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def predict(self,db):
    """
    predict embedding

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      
    Expected output (comma separated): 
      (float[n][d]) X : n-by-d embedding formatted of an n-length list of d-length lists of floats
      (int) num_reported_answers 
    """
    return NotImplementedError

  
