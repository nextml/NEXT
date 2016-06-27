import numpy as np
import utilsMDS
import time
import next.utils as utils
import random


class ValidationSampling:
    def initExp(self, butler, n, d, failure_probability):
        # params['query_list'] = [[11, 22, 0], [8, 12, 9], [14, 20, 6],
        #                         [19, 6, 16], [29, 15, 24], [26, 11, 29],
        #                         [22, 26, 5]]
        # formattted as [left, right, center] or [right, left, center]
        # (either one results in same behavior)
        X = np.random.randn(n, d)

        butler.algorithms.set(key='n', value=n)
        butler.algorithms.set(key='d', value=d)
        butler.algorithms.set(key='delta', value=failure_probability)
        butler.algorithms.set(key='X', value=X.tolist())

        params = butler.algorithms.get(key='params')  # alg specific parameters
        if params:
            if 'query_list' in params:
                query_list = params['query_list']

            elif 'num_tries' in params:
                num_tries = params['num_tries']
                query_list = []
                for i in range(num_tries):  # generate a lot of queries.
                    q, score = utilsMDS.getRandomQuery(X)
                    query_list.append(q)
        else:
            raise Exception("For ValidationSampling you must specifiy "
                            "'query_list' or 'num_tries'")

        butler.algorithms.set(key='query_list', value=query_list)
        butler.algorithms.set(key='do_not_ask', value=[])

        return True

    def getQuery(self, butler):
        utils.debug_print("Entering myAlg.getQuery")
        query_list = butler.algorithms.get(key='query_list')
        query_list = [query_list[i]
                      for i in np.random.permutation(len(query_list))]

        do_not_ask = butler.algorithms.get(key='do_not_ask')

        # enfore do_not_ask
        for q in do_not_ask:
            query_list.remove([q[0], q[1], q[2]])

        query = random.choice(query_list)

        # append the current query to do_not_ask
        butler.algorithms.append(key='do_not_ask', value=query)

        utils.debug_print("Exiting myAlg.getQuery")
        return query[2], query[0], query[1]

    def processAnswer(self, butler, center_id, left_id, right_id,
                      target_winner):
        utils.debug_print("Entering myAlg.processAnswer")
        if left_id == target_winner:
            q = [left_id, right_id, target_winner]
        else:
            q = [left_id, left_id, target_winner]

        butler.algorithms.append(key='S', value=q)

        n = butler.algorithms.get(key='n')
        num_answers = butler.algorithms.increment(key='num_reported_answers')

        if num_answers % int(n) == 0:
            args = {'task': '_full_embedding_update', 'task_args_json': {}}
            butler.job(time_limit=30, **args)
        else:
            args = {'task': '_incremental_embedding_update',
                    'task_args_json': {}}
            butler.job(time_limit=5, **args)

        utils.debug_print("Exiting myAlg.processAnswer")
        return True

    def getModel(self, butler):
        return butler.algorithms.get(key=['X', 'num_reported_answers'])

    def _incremental_embedding_update(self, butler, args):
        utils.debug_print("Entering _incremental_embedding_update")
        S = butler.algorithms.get(key='S')

        X = np.array(butler.algorithms.get(key='X'))

        # set maximum time allowed to update embedding
        t_max = 1.0

        # a relative convergence criterion, see computeEmbeddingWithGD
        # documentation
        epsilon = 0.01

        # take a single gradient step
        t_start = time.time()
        response = utilsMDS.computeEmbeddingWithGD(X, S, max_iters=1)
        X, emp_loss_new, hinge_loss_new, acc = response
        k = 1
        while (time.time() - t_start < 0.5*t_max) and (acc > epsilon):
            response = utilsMDS.computeEmbeddingWithGD(X, S, max_iters=2**k)
            X, emp_loss_new, hinge_loss_new, acc = response
            k += 1

        butler.algorithms.set(key='X', value=X.tolist())
        utils.debug_print("Leaving _incremental_embedding_update")

    def _full_embedding_update(self, butler, args):
        utils.debug_print("Entering _full_embedding_update")
        verbose = False

        n = butler.algorithms.get(key='n')
        d = butler.algorithms.get(key='d')
        S = butler.algorithms.get(key='S')

        X_old = np.array(butler.algorithms.get(key='X'))

        t_max = 5.0
        # a relative convergence criterion
        # see computeEmbeddingWithGD documentation
        epsilon = 0.01

        emp_loss_old, hinge_loss_old = utilsMDS.getLoss(X_old, S)
        X, tmp = utilsMDS.computeEmbeddingWithEpochSGD(n, d, S,
                                                       max_num_passes=16,
                                                       epsilon=0,
                                                       verbose=verbose)
        t_start = time.time()

        response = utilsMDS.computeEmbeddingWithGD(X, S, max_iters=1)
        X, emp_loss_new, hinge_loss_new, acc = response

        k = 1
        while (time.time() - t_start < 0.5*t_max) and (acc > epsilon):
            response = utilsMDS.computeEmbeddingWithGD(X, S, max_iters=2**k)
            X, emp_loss_new, hinge_loss_new, acc = response
            k += 1
        emp_loss_new, hinge_loss_new = utilsMDS.getLoss(X, S)
        if emp_loss_old < emp_loss_new:
            X = X_old
        butler.algorithms.set(key='X', value=X.tolist())
        utils.debug_print("Exiting _full_embedding_update")
