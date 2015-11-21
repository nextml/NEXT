"""
STE algorithm of the Online Learning Library for Next.Discovery
author: Lalit Jain, kevin.g.jamieson@gmail.com
last updated: 4/22/2015
"""
import numpy
import numpy.random
from next.apps.PoolBasedTripletMDS.algs.STE import utilsSTE
from next.apps.PoolBasedTripletMDS.Prototype import PoolBasedTripletMDSPrototype

import time

class STE(PoolBasedTripletMDSPrototype):

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


  def initExp(self,resource=None,n=0,d=0,failure_probability=0.05):
    X = numpy.random.randn(n,d)*.0001
    tau = numpy.random.rand(n,n)
    
    resource.set('n',n)
    resource.set('d',d)
    resource.set('delta',failure_probability)
    resource.set('X',X.tolist())
    resource.set('tau',tau.tolist())
    return True


  def getQuery(self,resource):
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
    best_q, best_score = utilsSTE.getRandomQuery(X)
    t_start = time.time()
    best_entropy = -1*float('inf')

    while time.time()-t_start<t_max:
      q,score = utilsSTE.getRandomQuery(X)
      b,c,a = q
      p = 0
      for i in range(n):
        p += utilsSTE.getSTETripletProbability(X[b],X[c],X[i]) * tau[a,i]

      taub = list(tau[a])
      for i in range(n):
        taub[i] = taub[i] * utilsSTE.getSTETripletProbability(X[b],X[c],X[i]) 
      taub = taub/sum(taub)
      
      tauc = list(tau[a])
      for i in range(n):
        tauc[i] = tauc[i] * utilsSTE.getSTETripletProbability(X[c],X[b],X[i]) 
      tauc = tauc/sum(tauc)
      
      entropy  = -p*utilsSTE.getEntropy(taub)-(1-p)*utilsSTE.getEntropy(tauc)

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
    alpha = 1
    
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsSTE.computeEmbeddingWithGD(X,S,alpha,max_iters=1, epsilon=epsilon,verbose=verbose)
    k = 1
    while (time.time()-t_start<.5*t_max) and (acc > epsilon):
      X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsSTE.computeEmbeddingWithGD(X,S,alpha,max_iters=2**k, epsilon=epsilon,verbose=verbose)
      k+=1

    tau = utilsSTE.getSTETauDistribution(X,S,alpha)

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
    alpha = 1

    emp_loss_old,hinge_loss_old,log_loss_old = utilsSTE.getLoss(X_old,S,alpha)
    X,tmp = utilsSTE.computeEmbeddingWithEpochSGD(n,d,S,alpha,max_num_passes=16,epsilon=0,verbose=verbose)
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsSTE.computeEmbeddingWithGD(X,S,alpha,max_iters=1, epsilon=epsilon,verbose=verbose)
    k = 1
    while (time.time()-t_start<.5*t_max) and (acc > epsilon):
      X,emp_loss_new,hinge_loss_new,log_loss_new,acc = utilsSTE.computeEmbeddingWithGD(X,S,alpha,max_iters=2**k, epsilon=epsilon,verbose=verbose)
      k += 1
    emp_loss_new,hinge_loss_new,log_loss_new = utilsSTE.getLoss(X,S, alpha)
    if emp_loss_old < emp_loss_new:
      X = X_old
    
    tau = utilsSTE.getSTETauDistribution(X,S,alpha)

    resource.set('X',X.tolist())
    resource.set('tau',tau.tolist())


