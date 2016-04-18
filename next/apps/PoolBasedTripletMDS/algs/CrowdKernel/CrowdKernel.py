"""
CrowdKernel algorithm of the Online Learning Library for Next.Discovery
author: Lalit Jain, kevin.g.jamieson@gmail.com
last updated: 4/22/2015
"""
import numpy
import numpy.random
from next.apps.PoolBasedTripletMDS.algs.CrowdKernel import utilsCrowdKernel
from next.apps.PoolBasedTripletMDS.Prototype import PoolBasedTripletMDSPrototype

import time

class CrowdKernel(PoolBasedTripletMDSPrototype):

  def daemonProcess(self,resource,daemon_args_dict):
    if 'task' in daemon_args_dict and 'args' in daemon_args_dict:
      task = daemon_args_dict['task']
      args = daemon_args_dict['args']
      if task == '__full_embedding_update':
        self.__full_embedding_update(resource,args)
      elif task == '__incremental_embedding_update':
        self.__incremental_embedding_update(resource,args)
    else:
      return False

    return True


  def initExp(self,resource,n,d,failure_probability,params):
    X = numpy.random.randn(n,d)*.0001
    tau = numpy.random.rand(n,n)
    
    resource.set('n',n)
    resource.set('d',d)
    resource.set('delta',failure_probability)
    resource.set('X',X.tolist())
    resource.set('tau',tau.tolist())
    # resource.set('S',[]) # do not initialize a list that you plan to append to! When you append_list the first item it will be created automatically.
    # resource.set('num_reported_answers',0) # do not initialize an incremental variable you plan to increment. When you increment for the first time it will initizliae the variable at 0.
    return True


  def getQuery(self,resource,do_not_ask_list):
    R = 10
    n = resource.get('n')
    d = resource.get('d')
    num_reported_answers = resource.get('num_reported_answers')
 
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
      return a, b, c

    X = numpy.array(resource.get('X'))
    tau = numpy.array(resource.get('tau'))


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

    return index_center,index_left,index_right

  
  def processAnswer(self,resource,index_center,index_left,index_right,index_winner):
    if index_left==index_winner:
      q = [index_left,index_right,index_center]
    else:
      q = [index_right,index_left,index_center]

    resource.append_list('S',q)

    n = resource.get('n')
    num_reported_answers = resource.increment('num_reported_answers')
    if num_reported_answers % int(n) == 0:
      daemon_args_dict = {'task':'__full_embedding_update','args':{}}
      resource.daemonProcess(daemon_args_dict,time_limit=30)
    else:
      daemon_args_dict = {'task':'__incremental_embedding_update','args':{}}
      resource.daemonProcess(daemon_args_dict,time_limit=5)

    return True
    
  def predict(self,resource):
    key_value_dict = resource.get_many(['X','num_reported_answers'])

    X = key_value_dict.get('X',[])
    num_reported_answers = key_value_dict.get('num_reported_answers',[])

    return X,num_reported_answers


  def __incremental_embedding_update(self,resource,args):   
    verbose = False
     
    n = resource.get('n')
    d = resource.get('d')
    S = resource.get_list('S')
    
    X = numpy.array(resource.get('X'))
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

    resource.set('X',X.tolist())
    resource.set('tau',tau.tolist())



  def __full_embedding_update(self,resource,args):
    verbose = False

    n = resource.get('n')
    d = resource.get('d')
    S = resource.get_list('S')

    X_old = numpy.array(resource.get('X'))
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

    resource.set('X',X.tolist())
    resource.set('tau',tau.tolist())






