from __future__ import print_function
import time
import numpy.random
from apps.PoolBasedTripletMDS.algs.RandomSampling import utilsMDS
import next.utils as utils


class MyAlg:
    def initExp(self, butler, n, d, failure_probability):
        X = numpy.random.randn(n, d)
        butler.algorithms.set(key="n", value=n)
        butler.algorithms.set(key="d", value=d)
        butler.algorithms.set(key="delta", value=failure_probability)
        butler.algorithms.set(key="X", value=X.tolist())
        butler.algorithms.set(key="num_reported_answers", value=0)
        return True

    def getQuery(self, butler):
        X = numpy.array(butler.algorithms.get(key="X"))
        q, score = utilsMDS.getRandomQuery(X)
        index_center = q[2]
        index_left = q[0]
        index_right = q[1]
        return [index_center, index_left, index_right]

    def processAnswer(self, butler, center_id, left_id, right_id, target_winner):
        if left_id == target_winner:
            q = [left_id, right_id, center_id]
        else:
            q = [right_id, left_id, center_id]
        butler.algorithms.append(key="S", value=q)
        n = butler.algorithms.get(key="n")
        num_reported_answers = butler.algorithms.increment(key="num_reported_answers")
        if num_reported_answers % int(n) == 0:
            butler.job("full_embedding_update", {}, time_limit=30)
        else:
            butler.job("incremental_embedding_update", {}, time_limit=5)
        return True

    def getModel(self, butler):
        return butler.algorithms.get(key=["X", "num_reported_answers"])

    def incremental_embedding_update(self, butler, args):
        S = butler.algorithms.get(key="S")
        X = numpy.array(butler.algorithms.get(key="X"))
        # set maximum time allowed to update embedding
        t_max = 1.0
        epsilon = (
            0.01
        )  # a relative convergence criterion, see computeEmbeddingWithGD documentation
        # take a single gradient step
        t_start = time.time()
        X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
            X, S, max_iters=1
        )
        k = 1
        while (time.time() - t_start < 0.5 * t_max) and (acc > epsilon):
            X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
                X, S, max_iters=2 ** k
            )
            k += 1
        butler.algorithms.set(key="X", value=X.tolist())

    def full_embedding_update(self, butler, args):
        n = butler.algorithms.get(key="n")
        d = butler.algorithms.get(key="d")
        S = butler.algorithms.get(key="S")

        X_old = numpy.array(butler.algorithms.get(key="X"))

        t_max = 5.0
        epsilon = (
            0.01
        )  # a relative convergence criterion, see computeEmbeddingWithGD documentation

        emp_loss_old, hinge_loss_old = utilsMDS.getLoss(X_old, S)
        X, tmp = utilsMDS.computeEmbeddingWithEpochSGD(
            n, d, S, max_num_passes=16, epsilon=0, verbose=False
        )
        t_start = time.time()
        X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
            X, S, max_iters=1
        )
        k = 1
        while (time.time() - t_start < 0.5 * t_max) and (acc > epsilon):
            X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
                X, S, max_iters=2 ** k
            )
            k += 1
        emp_loss_new, hinge_loss_new = utilsMDS.getLoss(X, S)
        if emp_loss_old < emp_loss_new:
            X = X_old
        butler.algorithms.set(key="X", value=X.tolist())
