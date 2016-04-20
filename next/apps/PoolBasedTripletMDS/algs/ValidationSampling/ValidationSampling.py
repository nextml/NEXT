"""
UncertaintySampling app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/17/2015
"""
import numpy.random
from next.apps.PoolBasedTripletMDS.algs.ValidationSampling import utilsMDS
from next.apps.PoolBasedTripletMDS.Prototype import PoolBasedTripletMDSPrototype

import time

class ValidationSampling(PoolBasedTripletMDSPrototype):

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


  def initExp(self,resource,n,d,failure_probability,params=None):
    # params['query_list'] = [[11, 22, 0], [8, 12, 9], [14, 20, 6], [19, 6, 16], [29, 15, 24], [26, 11, 29], [22, 26, 5]]
    # formattted as [left,right,center] or [right,left,center] (either one results in same behavior)
    X = numpy.random.randn(n,d)

    resource.set('n',n)
    resource.set('d',d)
    resource.set('delta',failure_probability)
    resource.set('X',X.tolist())

    if params:
      if 'query_list' in params:
        query_list = params['query_list']
      elif 'num_tries' in params:
        num_tries = params['num_tries']
        query_list = []
        for i in range(num_tries): # generate a lot of queries. 
          q,score = utilsMDS.getRandomQuery(X)
          query_list.append(q)
    else:
      raise Exception('For ValidationSampling you must specifiy \'query_list\' or \'num_tries\'')

    resource.set('query_list',query_list)


    return True


  def getQuery(self,resource,do_not_ask_list):
    query_list = numpy.array(resource.get('query_list'))
    rand_perm = numpy.random.permutation(len(query_list))
    query_list = [query_list[i] for i in rand_perm]

    asked_queries_hash = {}
    for q in do_not_ask_list:
      asked_queries_hash[ str([q[0],q[1],q[2]]) ] = True
      asked_queries_hash[ str([q[1],q[0],q[2]]) ] = True

    m=0
    while asked_queries_hash.get( str([query_list[m][0],query_list[m][1],query_list[m][2]]), False):
      m+=1
      if m==len(query_list):
        break
    if m==len(query_list):
      q = query_list[numpy.random.choice(m)]
    else:
      q = query_list[m]      

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



