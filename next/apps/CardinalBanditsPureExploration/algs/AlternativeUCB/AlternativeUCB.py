import numpy
from next.apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype

class AlternativeUCB(CardinalBanditsPureExplorationPrototype):

  def initExp(self,resource,n,R,failure_probability):
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.set('R',R)
    resource.increment('total_pulls',0)
    UCB = []
    prec = []
    mu = []
    for i in range(n):
      UCB.append(float('inf'))
      mu.append(-1)
      prec.append(-1)
    resource.set('UCB',UCB)
    resource.set('mu',mu)
    resource.set('prec',prec)
    return True

  def getQuery(self,resource,do_not_ask_list):
    UCB = resource.get('UCB')
    index = numpy.argmax(UCB)
    return index

  def processAnswer(self,resource,target_index,target_reward):
    resource.increment('total_pulls',1)
    resource.append_list('answer_pairs',(target_index,target_reward))
    daemon_args_dict = {}
    resource.daemonProcess(daemon_args_dict)    
    return True

  def daemonProcess(self,resource,daemon_args_dict):
    answer_pairs = resource.get_list('answer_pairs')
    n = resource.get('n')
    R = resource.get('R')
    delta = resource.get('failure_probability')

    sumX = numpy.zeros(n)
    T = numpy.zeros(n)
    for answer in answer_pairs:
      target_index,target_reward = answer
      sumX[target_index] += target_reward
      T[target_index] += 1.

    mu = numpy.zeros(n)
    UCB = numpy.zeros(n)
    prec = numpy.zeros(n)
    for i in range(n):
      if T[i]==0:
        mu[i] = -1
        UCB[i] = float('inf')
        prec[i] = -1
      else:
        mu[i] = sumX[i] / T[i]
        UCB[i] = mu[i] + 2.*numpy.sqrt( 2.0*R*R*numpy.log( 4*T[i]*T[i]/delta ) / T[i] )
        prec[i] = numpy.sqrt( R*R  / float(T[i]) )
    
    resource.set('UCB',UCB.tolist())
    resource.set('mu',mu.tolist())
    resource.set('prec',prec.tolist())
    return True

  def predict(self,resource):
    mu = resource.get('mu')
    prec = resource.get('prec')
    return mu,prec