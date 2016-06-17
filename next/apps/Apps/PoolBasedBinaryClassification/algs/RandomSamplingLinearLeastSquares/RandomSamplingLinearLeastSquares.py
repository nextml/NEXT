import time
import numpy.random
from next.apps.Apps.PoolBasedBinaryClassification.Prototype import PoolBasedBinaryClassificationPrototype

class RandomSamplingLinearLeastSquares(PoolBasedBinaryClassificationPrototype):
  def initExp(self,butler, n, failure_probability,params):
    butler.algorithms.set(key='n',value= n)
    butler.algorithms.set(key='delta',value= failure_probability)
    target = butler.targets.get_target_item(butler.exp_uid,0) # assume feature dimension consistent across all targets
    d = len(target['meta']['features'])
    butler.algorithms.set(key='d',value= d)

    w = numpy.zeros(d+1).tolist()
    butler.algorithms.set(key='weights',value=w)

    return True


  def getQuery(self,butler, participant_uid):
    n = butler.algorithms.get(key='n')
    idx = numpy.random.choice(n)

    return idx


  def processAnswer(self,butler,target_index,target_label):
    butler.algorithms.append(key='S',value=(target_index,target_label))
    d = butler.algorithms.get(key='d')
    num_reported_answers = butler.algorithms.increment(key='num_reported_answers')
    if num_reported_answers % int(d) == 0:
      butler.job('full_embedding_update', {}, time_limit=30)

    return True


  def getModel(self, butler):
    return butler.algorithms.get(key=['weights','num_reported_answers'])


  def full_embedding_update(self,butler,args):
    answer_pairs = butler.algorithms.get(key='S')
    targets = butler.targets.get_targetset(butler.exp_uid)
    targets = sorted(targets,key=lambda x: x['target_id'])
    target_features = []
    for target_index in range(len(targets)):
      target_vec = targets[target_index]['meta']['features']
      target_vec.append(1.)
      target_features.append(target_vec)

    X = []
    y = []
    for answer in answer_pairs:
      target_index,target_label = answer
      X.append(target_features[target_index])
      y.append(target_label)
    X = numpy.array(X)
    y = numpy.array(y)
    w = numpy.linalg.lstsq(X,y)[0]
    # label_residues = numpy.dot(X,w)
    butler.algorithms.set(key='weights',value=w.tolist())



