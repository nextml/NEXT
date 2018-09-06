"""
UncertaintySampling app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/17/2015
"""
from __future__ import print_function
import numpy
import numpy as np
import numpy.random
import random
import next.utils as utils
from apps.PoolBasedTripletMDS.algs.UncertaintySampling import utilsMDS
import time


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
        n = butler.algorithms.get(key="n")
        d = butler.algorithms.get(key="d")
        # If number of reported answers is small, generate random to avoid overfitting
        num_reported_answers = butler.algorithms.get(key="num_reported_answers")
        if num_reported_answers == None:
            num_reported_answers = 0
        R = int(1 + d * numpy.log(n))
        if num_reported_answers < R * n:
            # This generates the same shuffle every time this everytime
            # TODO: but this in utils and call this from other algorithms (they use
            # the same method).
            r = random.Random()
            r.seed(42)
            idxs = np.arange(n).repeat(R).tolist()
            r.shuffle(idxs)

            a = idxs[num_reported_answers]
            b = numpy.random.randint(n)
            while b == a:
                b = numpy.random.randint(n)
            c = numpy.random.randint(n)
            while c == a or c == b:
                c = numpy.random.randint(n)
            return [a, b, c]
        # generate an active query
        X = numpy.array(butler.algorithms.get(key="X"))
        # set maximum time allowed to search for a query
        t_max = 0.05
        q, signed_score = utilsMDS.getRandomQuery(X)
        best_q = q
        best_score = abs(signed_score)
        t_start = time.time()
        while time.time() - t_start < t_max:
            q, signed_score = utilsMDS.getRandomQuery(X)
            if abs(signed_score) < best_score:
                best_q = q
                best_score = abs(signed_score)
        index_center = best_q[2]
        index_left = best_q[0]
        index_right = best_q[1]
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
        verbose = False
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
            X, S, max_iters=1, verbose=verbose
        )
        k = 1
        while (time.time() - t_start < 0.5 * t_max) and (acc > epsilon):
            # take a single gradient step
            X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
                X, S, max_iters=2 ** k, verbose=verbose
            )
            k += 1
        butler.algorithms.set(key="X", value=X.tolist())

    def full_embedding_update(self, butler, args):
        verbose = False
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
            n, d, S, max_num_passes=16, epsilon=0, verbose=verbose
        )
        t_start = time.time()
        X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
            X, S, max_iters=1, verbose=verbose
        )
        k = 1
        while (time.time() - t_start < 0.5 * t_max) and (acc > epsilon):
            X, emp_loss_new, hinge_loss_new, acc = utilsMDS.computeEmbeddingWithGD(
                X, S, max_iters=2 ** k, verbose=verbose
            )
            k += 1
        emp_loss_new, hinge_loss_new = utilsMDS.getLoss(X, S)
        if emp_loss_old < emp_loss_new:
            X = X_old
        butler.algorithms.set(key="X", value=X.tolist())
