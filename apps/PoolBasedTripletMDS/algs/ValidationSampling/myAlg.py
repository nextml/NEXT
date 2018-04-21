import numpy as np
import utilsMDS
import time
import next.utils as utils
import random


class MyAlg:
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
        butler.algorithms.set(key='num_reported_answers', value=0)

        params = butler.algorithms.get(key='params')  # alg specific parameters
        if params:
            if 'query_list' in params:
                query_list = params['query_list']
                if isinstance(query_list[0][0], str):
                    query_list = utils.filenames_to_ids(query_list, butler.targets)

            elif 'num_tries' in params:
                num_tries = params['num_tries']
                query_list = []
                for i in range(num_tries):  # generate a lot of queries.
                    q, score = utilsMDS.getRandomQuery(X)
                    query_list.append(q)
        else:
            raise Exception("For ValidationSampling you must specifiy "
                            "'query_list' or 'num_tries'")

        butler.algorithms.set(key='do_not_ask', value=[])
        butler.algorithms.set(key='query_list', value=query_list)

        return True

    def getQuery(self, butler):
        num_ans = butler.algorithms.get(key='num_reported_answers')
        query_list = butler.algorithms.get(key='query_list')
        i = num_ans % len(query_list)

        query = query_list[i]
        #  butler.participants.set(key='query', value=query)

        # append the current query to do_not_ask
        #  butler.algorithms.append(key='do_not_ask', value=query)
        return query[2], query[0], query[1]

    def processAnswer(self, butler, center_id, left_id, right_id,
                      target_winner):
        if left_id == target_winner:
            q = [left_id, right_id, target_winner]
        else:
            q = [left_id, left_id, target_winner]

        butler.algorithms.append(key='S', value=q)

        # The following lines enforce "do not ask". The query list gets shorter
        # each time this function is called (and an question is answered).
        #  query_list = butler.participants.get(key='query_list')
        #  query = butler.algorithms.get(key='query')
        #  query_list.remove(query)
        #  butler.participants.set(key='query_list', value=query_list)

        n = butler.algorithms.get(key='n')
        num_answers = butler.algorithms.increment(key='num_reported_answers')

        if num_answers % int(n) == 0:
            args = {'task': '_full_embedding_update', 'task_args_json': {}}
            butler.job(time_limit=30, **args)
        else:
            args = {'task': '_incremental_embedding_update',
                    'task_args_json': {}}
            butler.job(time_limit=5, **args)
        return True

    def getModel(self, butler):
        return butler.algorithms.get(key=['X', 'num_reported_answers'])

    def _incremental_embedding_update(self, butler, args):
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

    def _full_embedding_update(self, butler, args):
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
