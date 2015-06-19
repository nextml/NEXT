"""
UncertaintySampling app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/17/2015
"""
import numpy
import numpy.random
from next.apps.PoolBasedTripletMDS.UncertaintySampling import utilsMDS
from next.apps.PoolBasedTripletMDS.Prototype import PoolBasedTripletMDSPrototype

import time

class UncertaintySampling(PoolBasedTripletMDSPrototype):

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
    """
    initialize the experiment 

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) n : number of objects
      (int) d : desired dimension
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """

    X = numpy.random.randn(n,d)
    X2 = numpy.random.randn(n,2)

    resource.set('n',n)
    resource.set('d',d)
    resource.set('delta',failure_probability)
    resource.set('X',X.tolist())
    resource.set('X2',X2.tolist())
    # resource.set('S',[]) # do not initialize a list that you plan to append to! When you append_list the first item it will be created automatically.
    # resource.set('num_reported_answers',0) # do not initialize an incremental variable you plan to increment. When you increment for the first time it will initizliae the variable at 0.
    return True


  def getQuery(self,resource):
    """
    A request to ask which triplet to ask next

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 

    Expected output: 
      (int) index_center : index of arm must be in {0,1,2,...,n-1}
      (int) index_left : index of arm must be in {0,1,2,...,n-1} - index_center
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_center - index_left
    """
    n = resource.get('n')
    d = resource.get('d')

    # If number of reported answers is small, generate random to avoid overfitting
    num_reported_answers = resource.get('num_reported_answers')
    if num_reported_answers == None:
      num_reported_answers = 0
    
    R = int(1+d*numpy.log(n))
    if num_reported_answers < R*n:
      a = num_reported_answers/R
      b = numpy.random.randint(n)
      while b==a:
        b = numpy.random.randint(n)
      c = numpy.random.randint(n)
      while c==a or c==b:
        c = numpy.random.randint(n)
      return a, b, c


    # generate an active query
    X = numpy.array(resource.get('X'))

    # set maximum time allowed to search for a query
    t_max = 0.05 
    q,signed_score = utilsMDS.getRandomQuery(X)
    best_q = q
    best_score = abs(signed_score)

    t_start = time.time()
    while time.time()-t_start<t_max:
      q,signed_score = utilsMDS.getRandomQuery(X)
      if abs(signed_score) < best_score:
        best_q = q
        best_score = abs(signed_score)

    index_center = best_q[2]
    index_left = best_q[0]
    index_right = best_q[1]

    return index_center,index_left,index_right

  
  def processAnswer(self,resource,index_center,index_left,index_right,index_winner):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      (int) index_center : index of center object
      (int) index_left : index of left object
      (int) index_right : index of right object
      (int) index_winner : index of winner object, index_winner in {index_left,index_right}

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    
    if index_left==index_winner:
      q = [index_left,index_right,index_center]
    else:
      q = [index_right,index_left,index_center]

    resource.append_list('S',q)

    n = resource.get('n')
    d = resource.get('d')
    num_reported_answers = resource.increment('num_reported_answers')
    if num_reported_answers % int(n) == 0:
      daemon_args_dict = {'task':'__full_embedding_update','args':{}}
      resource.daemonProcess(daemon_args_dict,time_limit=30)
    else:
      daemon_args_dict = {'task':'__incremental_embedding_update','args':{}}
      resource.daemonProcess(daemon_args_dict,time_limit=5)

    return True


  def predict(self,resource,S):
    """
    
    """
    X = numpy.array(resource.get('X'))

    n,d = X.shape

    y = []
    for idx,q in enumerate(S):

      # returns 1.0 if predicts k closer to i than j, -1.0 otherwise
      y.append(numpy.sign(utilsMDS.getTripletScore(X,q)))

    return y

    
  def getStats(self,resource):
    """
    reports statistics on the experiment model or process

    Expected input:
      (next.database.DatabaseClient) resource : database client, can cell resource.set(key,value), value=resource.get(key) 
      
    Expected output (comma separated): 
      (float[n][d]) Xd : n-by-d embedding formatted of an n-length list of d-length lists of floats
      (float[n][2]) Xd : n-by-2 embedding formatted of an n-length list of 2-length lists of floats
    """

    X = numpy.array(resource.get('X'))
    X2 = numpy.array(resource.get('X2'))

    return X.tolist(),X2.tolist()


  def __incremental_embedding_update(self,resource,args):
    verbose = False

    n = resource.get('n')
    d = resource.get('d')
    S = resource.get_list('S')


    X = numpy.array(resource.get('X'))
    X2 = numpy.array(resource.get('X2'))
    # set maximum time allowed to update embedding
    t_max = 1.0
    epsilon = 0.01 # a relative convergence criterion, see computeEmbeddingWithGD documentation

    # take a single gradient step
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=1,verbose=verbose)
    k = 1
    while (time.time()-t_start<0.5*t_max) and (acc > epsilon):
      # take a single gradient step
      X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=2**k,verbose=verbose)
      k += 1

    if d==2:
      X2 = X
    else:
      # take a single gradient step
      t_start = time.time()
      X2,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X2,S,max_iters=1,verbose=verbose)
      k=1
      while (time.time()-t_start<0.5*t_max) and (acc > epsilon):      
        # take a single gradient step
        X2,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X2,S,max_iters=2**k,verbose=verbose)
        k += 1

    resource.set('X',X.tolist())
    resource.set('X2',X2.tolist())

  def __full_embedding_update(self,resource,args):
    verbose = False

    n = resource.get('n')
    d = resource.get('d')
    S = resource.get_list('S')

    X_old = numpy.array(resource.get('X'))
    X2_old = numpy.array(resource.get('X2'))

    t_max = 5.0
    epsilon = 0.01 # a relative convergence criterion, see computeEmbeddingWithGD documentation

    emp_loss_old,hinge_loss_old = utilsMDS.getLoss(X_old,S)
    X,tmp = utilsMDS.computeEmbeddingWithEpochSGD(n,d,S,max_num_passes=16,epsilon=0,verbose=verbose)
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=1,verbose=verbose)
    k = 1
    while (time.time()-t_start<0.5*t_max) and (acc > epsilon):
      # take a single gradient step
      X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=2**k,verbose=verbose)
      k += 1
    emp_loss_new,hinge_loss_new = utilsMDS.getLoss(X,S)
    if emp_loss_old < emp_loss_new:
      X = X_old
    resource.set('X',X.tolist())

    if d==2:
      X2 = X
    else:
      emp_loss_old,hinge_loss_old = utilsMDS.getLoss(X2_old,S)
      X2,tmp = utilsMDS.computeEmbeddingWithEpochSGD(n,2,S,max_num_passes=16,epsilon=0,verbose=verbose)
      t_start = time.time()
      X2,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X2,S,max_iters=1,verbose=verbose)
      k = 1
      while (time.time()-t_start<0.5*t_max) and (acc > epsilon):      
        # take a single gradient step
        X2,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X2,S,max_iters=2**k,verbose=verbose)
        k += 1
      emp_loss_new,hinge_loss_new = utilsMDS.getLoss(X2,S)
      if emp_loss_old < emp_loss_new:
        X2 = X2_old
      resource.set('X2',X2.tolist())

    
    

    



