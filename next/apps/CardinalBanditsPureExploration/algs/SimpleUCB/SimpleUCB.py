import numpy
from next.apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype

class SimpleUCB(CardinalBanditsPureExplorationPrototype):

  def initExp(self,resource,n,R,failure_probability):
    resource.set('n',n)
    resource.set('failure_probability',failure_probability)
    resource.set('R',R)
    resource.increment('total_pulls',0)
    for i in range(n):
      resource.increment('Xsum_'+str(i),0.)
      resource.increment('T_'+str(i),0)

    return True

  
  def getQuery(self,resource,do_not_ask_list):
    n = resource.get('n')

    key_list = ['R','failure_probability']
    for i in range(n):
      key_list.append( 'Xsum_'+str(i) )
      key_list.append( 'T_'+str(i) )

    key_value_dict = resource.get_many(key_list)

    R = key_value_dict['R']
    delta = key_value_dict['failure_probability']

    sumX = []
    T = []
    for i in range(n):
      sumX.append( key_value_dict['Xsum_'+str(i)] )
      T.append( key_value_dict['T_'+str(i)] )

    T = numpy.array(T)
    mu = numpy.zeros(n)
    UCB = numpy.zeros(n)
    for i in range(n):
      if T[i]==0:
        mu[i] = float('inf')
        UCB[i] = float('inf')
      else:
        mu[i] = sumX[i] / T[i]
        UCB[i] = mu[i] + 2.*numpy.sqrt( 2.0*R*R*numpy.log( 4*T[i]*T[i]/delta ) / T[i] )

    index = numpy.argmax(UCB)

    return index

  def processAnswer(self,resource,target_index,target_reward):
    resource.increment_many({'Xsum_'+str(target_index):target_reward,'T_'+str(target_index):1,'total_pulls':1})
    
    return True

  def predict(self,resource):
    n = resource.get('n')

    key_list = ['R']
    for i in range(n):
      key_list.append( 'Xsum_'+str(i) )
      key_list.append( 'T_'+str(i) )

    key_value_dict = resource.get_many(key_list)
    R = key_value_dict['R']
    
    sumX = []
    T = []
    for i in range(n):
      sumX.append( key_value_dict['Xsum_'+str(i)] )
      T.append( key_value_dict['T_'+str(i)] )

    mu = numpy.zeros(n)
    prec = numpy.zeros(n)
    for i in range(n):
      if T[i]==0 or mu[i]==float('inf'):
        mu[i] = -1
        prec[i] = -1
      else:
        mu[i] = float(sumX[i]) / T[i]
        prec[i] = numpy.sqrt( R*R  / float(T[i]) )
    
    return mu.tolist(),prec.tolist()