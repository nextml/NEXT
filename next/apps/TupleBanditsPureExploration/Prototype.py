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

  def initExp(self,exp_uid,args_json):
    """
    initialize the project and necessary experiments 

    Expected input (in json structure with string keys):
      (int) n: number of arms
      (int) k: number of objects to display
      (float) failure_probability : confidence
      [optional] (list of dicts) alg_list : with fields (Defaults given by Info.get_app_default_alg_list)
            (string) alg_id : valid alg_id for this app_id
            (string) alg_label : unique identifier for algorithm (e.g. may have experiment with repeated alg_id's, but alg_labels must be unqiue, will also be used for plot legends
            [optional] (string) test_alg_label : must be one of the alg_label's in alg_list (Default is self)
      [optional] (dict) algorithm_management_settings : dictionary with fields (string) 'mode' and (dict) 'params'. mode in {'pure_exploration','explore_exploit','fixed_proportions'}. Default is 'fixed_proportions' and allocates uniform probability to each algorithm. If mode=fixed_proportions then params is a dictionary that contains the field 'proportions' which is a list of dictionaries with fields 'alg_label' and 'proportion' for all algorithms in alg_list. All proportions must be positive and sum to 1 over all algs in alg_list 
      [optional] (string) participant_to_algorithm_management : in {'one_to_one','one_to_many'}. Default is 'one_to_many'.
      [optional] (int) num_tries
    
    Expected output:
      if error:
        return (JSON) '{}', (bool) False, (str) error_str
      else:
        return (JSON) '{}', (bool) True,''
    """
    return NotImplementedError


  def getQuery(self,exp_uid,args_json):
    """
    A request to ask which k arms to duel next

    Expected input (in jsonstructure with string keys):
      (int) k : number of objects to display
      [optional] (string) participant_uid :  unique identifier of session for a participant answering questions (that is, an email address is not good enough as the participant could participate in multiple exp_uids so it would not be unique against all experiments), if key non-existant particpant_uid is assigned as exp_uid. 

    Expected output (in json structure with string keys):
      (list) target_indices : list of k target indexes e.g. [ (int) target_index_1, ... , (int) target_index_k ]
      (str) query_uid : unique identifier of query (used to look up for processAnswer)

    """
    return NotImplementedError

  
  def processAnswer(self,exp_uid,args_json):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (str) query_uid : unique identifier of query
      (int) index_winner : index of arm must be one of the indices given by getQuery

    Expected output (comma separated): 
      if error:
        return (JSON) '{}', (bool) False, (str) error
      else:
        return (JSON) '{}', (bool) True,''
    """
    return NotImplementedError

  def predict(self,exp_uid,args_json):
    """
    Description: uses current model empirical estimates to forecast the ranking of the arms in order of likelhood of being the best from most to least likely

    Expected input:
      (string) predict_id : 'arm_ranking'
      (dict) params : dictionary with fields
          (string) alg_label : describes target algorithm to use

    Expected output (in json structure):
      (list of dicts with fields):
        (int) index : index of target
        (int) rank : rank that the algorithm assigns to index (rank 0 is most likely the best arm)
    """
    return NotImplementedError

    
  def getStats(self,exp_uid,args_json):
    """
    Get statistics for the experiment and its algorithms

    Expected input (in json structure with string keys):
      (string) stat_id : identifier for the desired statistic
      (dict) params : dictionary of stat_id specific fields.

    See Next.utils.get_app_supported_stats(app_id) ResourceManager.get_app_supported_stats(app_id)
    for a description of each of the available stats and their inputs and outputs
    """
    return NotImplementedError


