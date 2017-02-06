"""
This algorithm is ongoing work with

* Ervin Tánczos <balambeer@gmail.com>
* Kevin Jamieson <kevin.g.jamieson@gmail.com>
* ROBERT D NOWAK <rdnowak@wisc.edu>

The Lil-UCB assumes that arbitrary numeric rewards can be given (sub-Gaussian
in particular). This KLUCB assumes that the rewards are bounded (and not
sub-Gaussian).

An academic paper is planning on arriving in "several months" (quoted on
2017-02-06)

"""

import numpy
import numpy.random

class MyAlg:

  def initExp(self,butler,n,R,failure_probability,params={}):
    butler.algorithms.set(key='n', value=n)
    butler.algorithms.set(key='delta',value=failure_probability)
    butler.algorithms.set(key='R',value=R)

    empty_list = numpy.zeros(n).tolist()
    butler.algorithms.set(key='Xsum',value=empty_list)
    butler.algorithms.set(key='X2sum',value=empty_list)
    butler.algorithms.set(key='T',value=empty_list)

    priority_list = numpy.random.permutation(n).tolist()
    butler.algorithms.set(key='priority_list',value=priority_list)

    return True

  
  def getQuery(self,butler,participant_uid):
    participant_dict = butler.participants.get(uid=participant_uid)
    do_not_ask_hash = {key: True for key in participant_dict.get('do_not_ask_list',[])}

    kv_dict = butler.algorithms.increment_many(key_value_dict={'priority_list':0,'priority_list_cnt':1}) 
    priority_list = kv_dict['priority_list']
    priority_list_cnt = kv_dict['priority_list_cnt']

    k = (priority_list_cnt-1) % len(priority_list)
    while k<len(priority_list) and do_not_ask_hash.get(priority_list[k],False):
      k+=1
    if k==len(priority_list):
      index = numpy.random.choice(priority_list)
    else:
      index = priority_list[k]

    return index

  def processAnswer(self,butler,target_id,target_reward): 
    butler.algorithms.append(key='S',value=(target_id,target_reward))

    if numpy.random.rand()<.1: # occurs about 1/10 of trials
#      update_priority_list(butler, time_limit=5)  # if want to call every time
      butler.job('update_priority_list', {},time_limit=5)

    return True

  def getModel(self,butler):
    key_value_dict = butler.algorithms.get()
    R = key_value_dict['R']
    n = key_value_dict['n']
    sumX = key_value_dict['Xsum']
    sumX2 = key_value_dict['X2sum']
    T = key_value_dict['T']

    mu = numpy.zeros(n)
    prec = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
        prec[i] = -1
      elif T[i]==1:
        mu[i] = float(sumX[i]) / T[i]
        prec[i] = R
      else:
        mu[i] = float(sumX[i]) / T[i]
        prec[i] = numpy.sqrt( float( max(1.,sumX2[i] - T[i]*mu[i]*mu[i]) ) / ( T[i] - 1. ) / T[i] )
    
    return mu.tolist(),prec.tolist(), T

  def update_priority_list(self,butler,args):
    S = butler.algorithms.get_and_delete(key='S')

    if S!=None:
      doc = butler.algorithms.get()

      R = doc['R']
      delta = doc['delta']
      n = doc['n']
      Xsum = doc['Xsum']
      X2sum = doc['X2sum']
      T = doc['T']

      for q in S:
        Xsum[q[0]] += q[1]
        X2sum[q[0]] += q[1]*q[1]
        T[q[0]] += 1

      mu = numpy.zeros(n)
      UCB = numpy.zeros(n)
      for i in range(n):
        if T[i]==0:
          mu[i] = float('inf')
          UCB[i] = float('inf')
        else:
          mu[i] = Xsum[i] / T[i]
          # UCB[i] = mu[i] + numpy.sqrt( 2.0*R*R*numpy.log( 4*T[i]*T[i]/delta ) / T[i] )
          # Note that the line below only makes sense when the responses take values in {1,2,3}
          UCB[i] = computeUCB(muhat=(mu[i]-1)/2,threshold=(numpy.log(2*T[i]*T[i]/delta)/T[i]))

      # sort by -UCB first then break ties randomly
      priority_list = numpy.lexsort((numpy.random.randn(n),-UCB)).tolist() 

      butler.algorithms.set_many(key_value_dict={'priority_list':priority_list,'priority_list_cnt':0,'Xsum':Xsum,'X2sum':X2sum,'T':T})

### Compute KL-UCB using binary bisection

### compute KL-UCB by repreatedly calling leftright until the desired accuracy is acheived (10^-6 by default)

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





