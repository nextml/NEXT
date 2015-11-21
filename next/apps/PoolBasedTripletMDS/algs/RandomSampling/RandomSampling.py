"""
UncertaintySampling app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/17/2015
"""
import numpy.random
from next.apps.PoolBasedTripletMDS.algs.RandomSampling import utilsMDS
from next.apps.PoolBasedTripletMDS.Prototype import PoolBasedTripletMDSPrototype

import time

class RandomSampling(PoolBasedTripletMDSPrototype):

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
    X = numpy.random.randn(n,d)

    resource.set('n',n)
    resource.set('d',d)
    resource.set('delta',failure_probability)
    resource.set('X',X.tolist())
    return True


  def getQuery(self,resource):
    X = numpy.array(resource.get('X'))

    q,score = utilsMDS.getRandomQuery(X)

    index_center = q[2]
    index_left = q[0]
    index_right = q[1]

    return index_center,index_left,index_right

  
  def processAnswer(self,resource,index_center,index_left,index_right,index_winner):
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
    epsilon = 0.01 # a relative convergence criterion, see computeEmbeddingWithGD documentation

    # take a single gradient step
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=1)
    k = 1
    while (time.time()-t_start<0.5*t_max) and (acc > epsilon):
      X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=2**k)
      k += 1

    resource.set('X',X.tolist())

  def __full_embedding_update(self,resource,args):
    verbose = False

    n = resource.get('n')
    d = resource.get('d')
    S = resource.get_list('S')

    X_old = numpy.array(resource.get('X'))

    t_max = 5.0
    epsilon = 0.01 # a relative convergence criterion, see computeEmbeddingWithGD documentation

    emp_loss_old,hinge_loss_old = utilsMDS.getLoss(X_old,S)
    X,tmp = utilsMDS.computeEmbeddingWithEpochSGD(n,d,S,max_num_passes=16,epsilon=0,verbose=verbose)
    t_start = time.time()
    X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=1)
    k = 1
    while (time.time()-t_start<0.5*t_max) and (acc > epsilon):
      X,emp_loss_new,hinge_loss_new,acc = utilsMDS.computeEmbeddingWithGD(X,S,max_iters=2**k)
      k += 1
    emp_loss_new,hinge_loss_new = utilsMDS.getLoss(X,S)
    if emp_loss_old < emp_loss_new:
      X = X_old
    resource.set('X',X.tolist())



