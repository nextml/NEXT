"""
CrowdKernel algorithm of the Online Learning Library for Next.Discovery
author: Lalit Jain, kevin.g.jamieson@gmail.com
last updated: 4/22/2015
"""
from __future__ import print_function
import numpy
import numpy.random
from apps.PoolBasedTripletMDS.algs.CrowdKernel import utilsCrowdKernel

import time

class MyAlg:

  def initExp(self,butler,n,d,failure_probability):
    X = numpy.random.randn(n,d)*.0001
    tau = numpy.random.rand(n,n)

    butler.algorithms.set(key='n',value=n)
    butler.algorithms.set(key='d',value=d)
    butler.algorithms.set(key='delta',value=failure_probability)
    butler.algorithms.set(key='X',value=X.tolist())
    butler.algorithms.set(key='tau',value=tau.tolist())
    # butler.algorithms.set(key='S',value=[]) # do not initialize a list that you plan to append to! When you append_list the first item it will be created automatically.
    butler.algorithms.set(key='num_reported_answers',value=0)
    return True


  def getQuery(self,butler):
    R = 10
    n = butler.algorithms.get(key='n')
    num_reported_answers = butler.algorithms.get(key='num_reported_answers')

    if num_reported_answers == None:
      num_reported_answers = 0

    if num_reported_answers < R*n:
      a = num_reported_answers/R
      b = numpy.random.randint(n)
      while b==a:
        b = numpy.random.randint(n)
      c = numpy.random.randint(n)
      while c==a or c==b:
        c = numpy.random.randint(n)
      return [a, b, c]

    X = numpy.array(butler.algorithms.get(key='X'))
    tau = numpy.array(butler.algorithms.get(key='tau'))

    # set maximum time allowed to search for a query
    t_max = .05
    best_q, best_score = utilsCrowdKernel.getRandomQuery(X)
    t_start = time.time()
    best_entropy = -1*float('inf')

    while time.time()-t_start<t_max:
      q,score = utilsCrowdKernel.getRandomQuery(X)
      b,c,a = q
      p = 0
      for i in range(n):
        p += utilsCrowdKernel.getCrowdKernelTripletProbability(X[b],X[c],X[i]) * tau[a,i]

      taub = list(tau[a])
      for i in range(n):
        taub[i] = taub[i] * utilsCrowdKernel.getCrowdKernelTripletProbability(X[b],X[c],X[i])
      taub = taub/sum(taub)

      tauc = list(tau[a])
      for i in range(n):
        tauc[i] = tauc[i] * utilsCrowdKernel.getCrowdKernelTripletProbability(X[c],X[b],X[i])
      tauc = tauc/sum(tauc)

      entropy  = -p*utilsCrowdKernel.getEntropy(taub)-(1-p)*utilsCrowdKernel.getEntropy(tauc)

      if entropy > best_entropy:
        best_q = q
        best_entropy = entropy
    index_center = best_q[2]
    index_left = best_q[0]
    index_right = best_q[1]
    return [index_center, index_left, index_right]


  def processAnswer(self,butler,center_id,left_id,right_id,target_winner):
    if left_id==target_winner:
      q = [left_id,right_id,center_id]
    else:
      q = [right_id,left_id,center_id]

    butler.algorithms.append(key='S',value=q)

    n = butler.algorithms.get(key='n')
    num_reported_answers = butler.algorithms.increment(key='num_reported_answers')
    if num_reported_answers % int(n) == 0:
      butler.job('full_embedding_update', {}, time_limit=30)
    else:
      butler.job('incremental_embedding_update', {},time_limit=5)

    return True

  def getModel(self,butler):
    return butler.algorithms.get(key=['X','num_reported_answers'])

  def incremental_embedding_update(self,butler,args):
    verbose = False
    S = butler.algorithms.get(key='S')

    X = numpy.array(butler.algorithms.get(key='X'))
    
    # set maximum time allowed to update embedding
    t_max = 1.0
    epsilon = 0.00001 # a relative convergence criterion, see computeEmbeddingWithGD documentation
    mu = .05

    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsCrowdKernel.computeEmbeddingWithGD(X,S,mu,epsilon=epsilon,max_iters=1)
    k = 1
    while (time.time()-t_start<.5*t_max) and (acc > epsilon):
      X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsCrowdKernel.computeEmbeddingWithGD(X,S,mu,max_iters=2**k, epsilon=epsilon, verbose=verbose)
      k+=1

    tau = utilsCrowdKernel.getCrowdKernelTauDistribution(X,S,mu)

    butler.algorithms.set(key='X',value=X.tolist())
    butler.algorithms.set(key='tau',value=tau.tolist())
    

  def full_embedding_update(self,butler,args):
    verbose = False

    n = butler.algorithms.get(key='n')
    d = butler.algorithms.get(key='d')
    S = butler.algorithms.get(key='S')

    X_old = numpy.array(butler.algorithms.get(key='X'))
    # set maximum time allowed to update embedding
    t_max = 5.0
    epsilon = 0.00001 # a relative convergence criterion, see computeEmbeddingWithGD documentation
    mu = .05


    emp_loss_old,hinge_loss_old,log_loss_old = utilsCrowdKernel.getLoss(X_old,S)
    X,tmp = utilsCrowdKernel.computeEmbeddingWithEpochSGD(n,d,S,mu,max_num_passes=16,epsilon=0,verbose=verbose)
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsCrowdKernel.computeEmbeddingWithGD(X,S,mu,max_iters=1,epsilon=epsilon,verbose=verbose)
    k = 1
    while (time.time()-t_start<.5*t_max) and (acc > epsilon):
      X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsCrowdKernel.computeEmbeddingWithGD(X,S,mu,max_iters=2**k,epsilon=epsilon,verbose=verbose)
      k += 1
    emp_loss_new,hinge_loss_new,log_loss_new = utilsCrowdKernel.getLoss(X,S)
    if emp_loss_old < emp_loss_new:
      X = X_old

    tau = utilsCrowdKernel.getCrowdKernelTauDistribution(X,S,mu)

    butler.algorithms.set(key='X',value=X.tolist())
    butler.algorithms.set(key='tau',value=tau.tolist())






