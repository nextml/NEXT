import numpy as np
import utilsMDS
import time
import next.utils as utils
import random


def getRandomQuery(n):
    a = np.random.choice(n)
    while True:
        b = np.random.choice(n)
        if a == b:
            return [a, b]


class ValidationSampling:
    def initExp(self, butler, n=None, failure_probability=None):
        butler.algorithms.set(key='n', value=n)
        butler.algorithms.set(key='failure_probability',
                              value=failure_probability)

        alg = butler.algorithms.get()
        params = alg.get(u'params', None)
        butler.algorithms.set(key='params', value=params)

        if params:
            if 'query_list' in params:
                query_list = params['query_list']

            elif 'num_tries' in params:
                num_tries = params['num_tries']
                query_list = [getRandomQuery(n) for _ in range(num_tries)]
            else:
                raise ValueError('Either specify "query_list" or "num_tries" '
                                 'in params')
        else:
            raise Exception("For ValidationSampling you must specifiy "
                            "'query_list' or 'num_tries' in params")

        arm_key_value_dict = {}
        for i in range(n):
            arm_key_value_dict['Xsum_'+str(i)] = 0.
            arm_key_value_dict['T_'+str(i)] = 0.

        arm_key_value_dict.update({'total_pulls': 0})

        butler.algorithms.set(key='query_list', value=query_list)

        butler.algorithms.set(key='keys', value=list(arm_key_value_dict.keys()))
        butler.algorithms.set_many(key_value_dict=arm_key_value_dict)

        return True

    def getQuery(self, butler, participant_uid):
        num_ans = butler.algorithms.get(key='total_pulls')
        query_list = butler.algorithms.get(key='query_list')
        i = num_ans % len(query_list)

        query = query_list[i]
        return query + [query[0]]

    def processAnswer(self, butler, left_id, right_id, painted_id, winner_id):
        butler.algorithms.increment_many(key_value_dict=
                                         {'Xsum_'+str(painted_id): 1.0,
                                          'T_'+str(painted_id): 1.0,
                                          'total_pulls': 1})

        # The following lines enforce "do not ask". The query list gets shorter
        # each time this function is called (and an question is answered).
        #  query_list = butler.participants.get(key='query_list')
        #  query = butler.algorithms.get(key='query')
        #  query_list.remove(query)
        #  butler.participants.set(key='query_list', value=query_list)

        return True

    def getModel(self, butler):
        keys = butler.algorithms.get(key='keys')
        key_value_dict = butler.algorithms.get(key=keys)
        n = butler.algorithms.get(key='n')

        sumX = [key_value_dict['Xsum_'+str(i)] for i in range(n)]
        T = [key_value_dict['T_'+str(i)] for i in range(n)]

        mu = np.zeros(n, dtype='float')
        for i in range(n):
            if T[i] == 0 or mu[i] == float('inf'):
                mu[i] = -1
            else:
                mu[i] = sumX[i] * 1.0 / T[i]

        prec = [np.sqrt(1.0/max(1, t)) for t in T]
        return mu.tolist(), prec
