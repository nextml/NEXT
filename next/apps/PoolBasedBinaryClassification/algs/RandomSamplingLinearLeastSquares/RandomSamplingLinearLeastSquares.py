import numpy
from next.apps.PoolBasedBinaryClassification.Prototype import PoolBasedBinaryClassificationPrototype

class RandomSamplingLinearLeastSquares(PoolBasedBinaryClassificationPrototype):

  def initExp(self,resource,example_pool,failure_probability,params):
    """
    Begin by normalizing examples so that they are zero mean and variance 1. If A is this normalized example example_pool 
    then let X = [A, ones(n,1)] be the matrix appended with a row of ones. 
    If labels is an array corresponding to observed labels of indices in another array idx, if we solve 
    argmin_w ||X[idx,:]*w-Y[idx]||^2 for w then sign(X*w) provides predictions for all the other labels.  
    """
    A = numpy.array(example_pool)
    n,d = A.shape
    mu = numpy.mean(A,axis=0)
    sigma = numpy.std(A,axis=0)
    for i in range(n):
      A[i] = (A[i]-mu)/sigma
    X = numpy.concatenate((A, numpy.ones( (n,1) ) ), axis=1)
    w = numpy.zeros(d+1)

    resource.set('n',n)
    resource.set('w',w.tolist())
    resource.set('example_pool',X.tolist())
    resource.set('failure_probability',failure_probability)

  def getQuery(self,resource,do_not_ask_list):
    n = resource.get('n')
    priority_list = numpy.random.permutation(n)

    k = 0
    while k<len(priority_list) and (priority_list[k] in do_not_ask_list): 
      k+=1
    if k==len(priority_list):
      index = numpy.random.randint(n)
    else:
      index = priority_list[k]

    return index
  
  def processAnswer(self,resource,target_index,target_label):
    resource.append_list('answer_pairs',(target_index,target_label))
    daemon_args_dict = {}
    resource.daemonProcess(daemon_args_dict)    
    return True

  def daemonProcess(self,resource,daemon_args_dict):
    example_pool = resource.get('example_pool')
    answer_pairs = resource.get_list('answer_pairs')
    X = []
    y = []
    for answer in answer_pairs:
      target_index,target_label = answer
      X.append(example_pool[target_index])
      y.append(target_label)
    X = numpy.array(X)
    y = numpy.array(y)
    w = numpy.linalg.lstsq(X,y)[0]
    resource.set('w',w.tolist())

  def predict(self,resource):
    w = resource.get('w')
    w = numpy.array(w)
    example_pool = resource.get_list('example_pool')
    labels = numpy.sign( numpy.dot(example_pool,w) )
    return labels
    

