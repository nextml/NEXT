from __future__ import print_function
import numpy
import numpy as np
import numpy.random
import next.utils as utils

class MyAlg:
  def initExp(self, butler, n, failure_probability, params=None):
    """
    This function is meant to set keys used later by the algorith implemented
    in this file.
    """
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='failure_probability', value=failure_probability)

    arm_key_value_dict = {}
    for i in range(n):
      arm_key_value_dict['Xsum_'+str(i)] = 0.
      arm_key_value_dict['T_'+str(i)] = 0.
    arm_key_value_dict.update({'total_pulls':0})

    butler.algorithms.set(key='keys', value=list(arm_key_value_dict.keys()))
    butler.algorithms.set_many(key_value_dict=arm_key_value_dict)

    return True

  def getQuery(self, butler, participant_uid):
    beta = 0.0 # algorithm parameter

    keys = butler.algorithms.get(key='keys')
    key_value_dict = butler.algorithms.get(key=keys)
    delta = butler.algorithms.get(key='failure_probability')
    n = butler.algorithms.get(key='n')

    sumX = [key_value_dict['Xsum_'+str(i)] for i in range(n)]
    T = [key_value_dict['T_'+str(i)] for i in range(n)]

    sigma_sq = 0.25

    mu = numpy.zeros(n)
    UCB = numpy.zeros(n)
    A = []
    for i in range(n):
      if T[i]==0:
        mu[i] = float('inf')
        UCB[i] = float('inf')
        A.append(i)
      else:
        # T[i] is the number of times arm has been pulled
        # X[i] is incrememnted by 0 or 1 depending on answer.
        mu[i] = sumX[i] / T[i]
        threshold = np.log(2 * T[i]**2 / delta) / T[i]
        UCB[i] = computeUCB(muhat=mu[i], threshold=threshold)

    if len(A)>0:
      index = numpy.random.choice(A)
    else:
      index = numpy.argmax(UCB)

    alt_index = numpy.random.choice(n)
    while alt_index==index:
      alt_index = numpy.random.choice(n)

    random_fork = numpy.random.choice(2)
    if random_fork==0:
      return [index,alt_index,index]
    else:
      return [alt_index,index,index]


  def processAnswer(self,butler, left_id=0, right_id=0, painted_id=0, winner_id=0):
    alt_index = left_id
    if left_id==painted_id:
      alt_index = right_id

    reward = 0.
    if painted_id==winner_id:
      reward = 1.

    butler.algorithms.increment_many(key_value_dict={'Xsum_'+str(painted_id):reward,
                                                     'T_'+str(painted_id):1.,
                                                     'total_pulls':1})

    return True

  def getModel(self,butler):
    keys = butler.algorithms.get(key='keys')
    key_value_dict = butler.algorithms.get(key=keys)

    n = butler.algorithms.get(key='n')

    sumX = [key_value_dict['Xsum_'+str(i)] for i in range(n)]
    T = [key_value_dict['T_'+str(i)] for i in range(n)]

    mu = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
      else:
        mu[i] = sumX[i] / T[i]

    prec = [numpy.sqrt(1.0/max(1,t)) for t in T]

    return mu.tolist(), prec

def computeUCB(muhat,threshold,accuracy=(10**(-6))):
  lower=muhat
  upper=1
  UCB=(lower+upper)/2
  while (upper-lower)>accuracy:
    new=leftright(muhat,lower,upper,threshold)
    lower=new[0]
    upper=new[1]
    UCB=new[2]
  return UCB

### leftright is the core funciton, decides which way to proceed with the bisection

def leftright(muhat,lower,upper,threshold):
  if muhat*(1-muhat)!=0:
    shit=(upper+lower)/2
    KL=(muhat*numpy.log(muhat/shit))+((1-muhat)*numpy.log((1-muhat)/(1-shit)))
    if KL>=threshold:
      return [lower,shit,(shit+lower)/2]
    if KL<threshold:
      return [shit,upper,(shit+upper)/2]
  if muhat==0:
    shit=(upper+lower)/2
    KL=(1-muhat)*numpy.log((1-muhat)/(1-shit))
    if KL>=threshold:
      return [lower,shit,(shit+lower)/2]
    if KL<threshold:
      return [shit,upper,(shit+upper)/2]
  if muhat==1:
    return [1,1,1]
