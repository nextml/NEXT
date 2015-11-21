"""
RandomSampling app implements TupleBanditsPureExplorationPrototype
author: Nick Glattard, n.glattard@gmail.com
last updated: 4/27/2015
"""

import numpy
import numpy.random
from next.apps.TupleBanditsPureExploration.Prototype import TupleBanditsPureExplorationPrototype

class RandomSampling(TupleBanditsPureExplorationPrototype):

  def daemonProcess(self,resource,daemon_args_dict):

    if 'task' in daemon_args_dict and 'args' in daemon_args_dict:
      task = daemon_args_dict['task']
      args = daemon_args_dict['args']
      if task == '__update_sufficient_statistics':
        self.__update_sufficient_statistics(resource,args)
    else:
      return False

    return True
  
  def initExp(self,resource,n=0,k=0,failure_probability=0.05):
    running_wins_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()

    resource.set('n',n)
    resource.set('k',k)
    resource.set('failure_probability',failure_probability)
    resource.set('running_wins_vec',running_wins_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',0)

    return True

  
  def getQuery(self,resource):
    # get parameters of experiment
    n = resource.get('n')
    k = resource.get('k')

    # create list to populate with target indices
    targets = numpy.random.choice(n,k,replace=False).tolist()

    return targets

  def processAnswer(self,resource,targets,index_winner=0):
    # q is the list of targets with the index winner at index 0
    q = targets
    q.remove(index_winner)
    q.insert(0,index_winner)
    resource.append_list('S',q)

    daemon_args_dict = {'task':'__update_sufficient_statistics','args':{}}
    resource.daemonProcess(daemon_args_dict,time_limit=1)
    
    return True

  def predict(self,resource):
    n = resource.get('n')
    T = resource.get('num_pulls_vec')
    wins_vec = resource.get('running_wins_vec')

    mu = [ 1.0*wins_vec[i]/max(1.,T[i]) for i in range(n)]
    prec = [ numpy.sqrt(1.0/max(1.,t)) for t in T]
    
    return mu,prec
    
  def __update_sufficient_statistics(self,resource,args):

    n = resource.get('n')
    S = resource.get_list('S')

    running_wins_vec = numpy.zeros(n).tolist()
    num_pulls_vec = numpy.zeros(n).tolist()

    # loop through query report answers
    for q in S:
      index_winner = q[0]

      running_wins_vec[index_winner] += 1
      for idx in q:
        num_pulls_vec[idx] += 1

    total_pulls = len(S)

    resource.set('running_wins_vec',running_wins_vec)
    resource.set('num_pulls_vec',num_pulls_vec)
    resource.set('total_pulls',total_pulls)

