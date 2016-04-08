import time
import numpy.random
from next.apps.Apps.PoolBasedBinaryClassification.Prototype import PoolBasedBinaryClassificationPrototype

class RandomSamplingLinearLeastSqaures(PoolBasedBinaryClassificationPrototype):
  def initExp(self,butler, n, failure_probability,params):
    butler.algorithms.set(key='n',value= n)
    butler.algorithms.set(key='delta',value= failure_probability)
    target = butler.targets.get_target_item(butler.exp_uid,0) # assume feature dimension consistent across all targets
    d = len(target['meta']['features'])
    butler.algorithms.set(key='d',value= d)

    w = numpy.zeros(d+1).tolist()
    butler.algorithms.set(key='weights',value=w)

    return True


  def getQuery(self,butler,participant_dict,**kwargs):
    n = butler.algorithms.get(key='n')
    idx = numpy.random.choice(n)
    # target = butler.targets.get_target_item(butler.exp_uid,idx)
    # x = numpy.array(target['meta']['features'])   # target['meta']['features'] is a list

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
    answer_pairs = butler.algorithms.get('S')
    targets = butler.targets.get_targetset(butler.exp_uid)
    targets = sorted(targets,key=lambda x: x['target_id'])

    X = []
    y = []
    for answer in answer_pairs:
      target_index,target_label = answer
      X.append(targets[target_index]['meta']['features'].append(1.))
      y.append(target_label)
    X = numpy.array(X)
    y = numpy.array(y)
    w = numpy.linalg.lstsq(X,y)[0]
    butler.algorithms.set(key='weights',value=w.tolist())



