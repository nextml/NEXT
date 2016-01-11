"""
PoolBasedBinaryClassification app of the Online Learning Library for Next.Discovery

PoolBasedBinaryClassificationPrototype

This interface must be implemented by an algorithm that for PoolBasedBinaryClassification. 
In this task, the user is shown a target and asked to answer a binary question about the target (e.g. 'Is this a cat, yes or no').  
The algorithm decides which target to show from among a fixed set of targets set at the initialization of the algorithm.
The objective is to predict the correct label (plus or minus 1) for all targets in the uploaded pool  
"""


class PoolBasedBinaryClassificationPrototype(object):
  def __init__(self): 
    self.app_id = 'PoolBasedBinaryClassification'

  def initExp(self,resource,example_pool,failure_probability,params):
    """ 
    initialize the experiment 

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (float[n][d]) example_pool : n-by-d Python list of lists of floats describing the n examples from which the algorithm can choose to show the the participant 
      (float) failure_probability : confidence parameter
      (dict) params : algorithm-specific parameters (if none provided in alg_list of init experiment, params=None)

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def getQuery(self,resource):
    """
    A request to ask which index/arm to pull

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (list of int) do_not_ask_list : indices in {0,...,n-1} that the algorithm must not return. If there does not exist an index that is not in do_not_ask_list then any index is acceptable (this changes for each participant so they are not asked the same question twice)

    Expected output (comma separated): 
      (int) target_index : index of of example (in 0,n-1) to show to the participant
    """
    return NotImplementedError
  
  def processAnswer(self,resource,target_index,target_label):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 
      (int) target_index : index of example shown
      (int) target_reward : provided label of example shown (+1/-1)

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def predict(self,resource):
    """
    uses current model to return empirical estimates with uncertainties

    Expected input:
      (next.resource_client.ResourceClient) resource : resource client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output: 
      (list +1/-1) predictions : predicted labels of the example_pool given all labels up to the current time
    """
    return NotImplementedError
    