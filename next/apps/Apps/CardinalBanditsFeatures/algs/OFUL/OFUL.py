"""
* make mapping, targets to features
* work with Zappos dataset
2. generalize to n users, not 1 user
3. choose initial sampling arm
    * myApp.py getQuery/processAnswer help this
    * V, b, theta_hat need to be stored per user
    * add new key to butler.particpants[i]
* make launching easier

## 2016-05-17
### Features
* Download features from internet, assume images have been uploaded (it takes
about 3 hours to do via S3 from the university
* do_not_ask is implemented

### Bottlenecks
* argmax is really slow; it uses a for loop in Python. I'll look into using
    NumPy to speed this up. Extrapolating to 50k features, it will take about
    25 minutes to answer one question

| Trial | App.py:getQuery | myApp.py:getQuery | get_X * 2   | argmax | Total |
| load  | 2.27            | 0.24              | 1.93 (*1)   | 0      | 2.17  |
| q0    | 10.38           | 1.02              | 1.96 + 2.27 | 0      | 5.25  |
| q1    | 9.3             | 1.08              | 1.97 + 1.95 | 4.49   | 9.49  |
| q2    | 14.69           | 1.15              | 3.83 + 1.97 | 7.25   | 14.2  |
(run on 2016-05-18 10:00 on c3.large machine with 2k shoes)

| Trial | App.py:getQuery | myApp.py:getQuery | get_X * 2   | argmax | Total |
| load  | 2.28            | 0.13              | 2.0*1       | 0      | 2.38  |
| q0    | 9.69            | 1.28              | 2.03 + 2.04 | 4.54   | 9.89  |
(run on 2016-05-18 11:00 on r3.large machine with 2k shoes)

| Trial | App.py:getQuery | myApp.py:getQuery | get_X * 2   | argmax | Total |
| load  | 51.57           | 0.58              | 50.8*1      | -      | 51.38 |
| q0    | 115             | 1.11              | 50.5*1      | 58.7   |       |
| q1    | 116             | 1.24              | 51.1 + 50.8 | 63     |       |
(run on 2016-05-11:30 on r3.large machine with 50k shoes)

inverting V does not take the most time in argmax_reward
time to invert (1000, 1000) matrix = 0.0263409614563

*summary:* from this, we need to (a) optimize getting X and (b) optimize
argmax_reward

After speeding up get_X to on the order of 0.2secs:

| Trial | App.py getQuery |
| load | 0.36 secs |
| q0 | not written down|
| q1 | get_X: 0.144 + 0.02, time_to_invert: 2.2secs, argmax_reward = 65secs

So most of the time is spent in OFUL:argmax

After speeding up argmax:

| Function            | Time 1   | Time 2 | Time 3 | Time 4 |
| ------------------- | -----    | -----  | ------ |        |
| myApp:processAnswer | 1.00     | 1.1    | 0.4    | 0.33   |
| alg:processAnswer   | 2.35     | 1.2    | 1.50   | 1.14   |
| App:processAnswer   | 3.38     | 2.3    | 1.9    |        |
| myApp:getQuery      | 1.29     | 1.43   | 0.73   | 0.497  |
| alg:getQuery        | 0.49     | 0.39   | 1.56   | 0.45   |
| App:getQuery        | 3.42     | 3.2    | 2.7    |        |
| ------------------- | -------- |        |        |        |
| Total               | 6.8      |        |        |        |
"""

from __future__ import division
import numpy as np
from next.apps.Apps.CardinalBanditsFeatures.Prototype import CardinalBanditsFeaturesPrototype
import next.utils as utils
import time

# TODO: change this to 1
reward_coeff = 1.00

def timeit(fn_name=''):
    def timeit_(func, *args, **kwargs):
        def timing(*args, **kwargs):
            start = time.time()
            r = func(*args, **kwargs)
            utils.debug_print('')
            utils.debug_print("function {} took {} seconds".format(fn_name, time.time() - start))
            utils.debug_print('')
            return r
        return timing
    return timeit_

@timeit(fn_name="argmax_reward")
def argmax_reward(X, theta, invV, beta, do_not_ask=[], k=0):
    r"""
    Loop over all columns of X to solve this equation:

        \widehat{x} = \arg \min_{x \in X} x^T theta + k x^T V^{-1} x
    """
    # inv = np.linalg.inv
    # norm = np.linalg.norm
    # iV = np.linalg.inv(V)
    # rewards = [np.inner(X[:, c], theta) + k*np.inner(X[:, c], iV.dot(X[:, c]))
               # for c in range(X.shape[1])]
    # rewards = np.asarray(rewards)
    # return X[:, np.argmax(rewards)], np.argmax(rewards)
    sqrt = np.sqrt

    rewards = X.T.dot(theta) + sqrt(k)*sqrt(beta)
    mask = np.ones(X.shape[1], dtype=bool)
    mask[do_not_ask] = False
    rewards = rewards[mask]
    utils.debug_print("OFUL28: do_not_ask = {}".format(do_not_ask))
    return X[:, np.argmax(rewards)], np.argmax(rewards)

@timeit(fn_name="calc_reward")
def calc_reward(x, theta, R=2):
    return np.inner(x, theta) + R*np.random.randn()

@timeit(fn_name="get_feature_vectors")
def get_feature_vectors(butler):
    features = np.load('features.npy')
    utils.debug_print("OFUL.py 120, features.shape = {}".format(features.shape))
    return features

class OFUL(CardinalBanditsFeaturesPrototype):
    def initExp(self, butler, params=None, n=None, R=None,
                failure_probability=None):
        """
        initialize the experiment

        (int) n : number of arms
        (float) R : sub-Gaussian parameter, e.g. E[exp(t*X)]<=exp(t^2 R^2/2),
                    defaults to R=0.5 (satisfies X \in [0,1])
        (float) failure_probability : confidence
                imp note: delta
        (dict) params : algorithm-specific parameters (if none provided in
                        alg_list of init experiment, params=None)

        Expected output (comma separated):
          (boolean) didSucceed : did everything execute correctly
        """
        # setting the target matrix, a description of each target
        # X = np.asarray(params['X'])
        X = get_feature_vectors(butler)
        # theta_star = np.asarray(params['theta_star'])

        d = X.shape[0]  # number of dimensions in feature
        lambda_ = 1.0 / d
        # V = lambda_ * np.eye(d)
        R = 2.0

        # initial sampling arm
        # theta_hat = X[:, np.random.randint(X.shape[1])]
        # theta_hat = np.random.randn(d)
        # theta_hat /= np.linalg.norm(theta_hat)

        to_save = {#'X': X.tolist(),
                   'R': R, 'd': d, 'n': n,
                   'lambda_': lambda_,
                   'total_pulls': 0.0,
                   'rewards': [],
                   'arms_pulled': [],
                   'failure_probability': failure_probability}

        for name in to_save:
            butler.algorithms.set(key=name, value=to_save[name])

        return True

    @timeit(fn_name='alg:getQuery')
    def getQuery(self, butler, participant_doc, exp_uid=None, args=None,
                 **kwargs):
        """
        A request to ask which index/arm to pull

        Expected input:
          (list of int) do_not_ask_list : indices in {0,...,n-1} that the
                algorithm must not return. If there does not exist an index
                that is not in do_not_ask_list then any index is acceptable
                (this changes for each participant so they are not asked the
                same question twice)

        Expected output (comma separated):
          (int) target_index : idnex of arm to pull (in 0,n-1)

         particpant_doc is butler.participants corresponding to this
         participant

        if we want, we can find some way to have different arms
        pulled using the butler
        """
        initExp = butler.algorithms.get()
        X = get_feature_vectors(butler) # np.asarray(initExp['X'], dtype=float)

        if not 'num_tries' in participant_doc.keys():
            participant_doc['participant_uid'] = args['participant_uid']
            participant_doc['num_tries'] = 0
            participant_doc['do_not_ask'] = []
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                         key_value_dict=participant_doc)
            return None

        if not 'invV' in participant_doc.keys():
            # * V, b, theta_hat need to be stored per user

            d = {'invV': (np.eye(initExp['d']) / initExp['lambda_']),
                 'beta': (np.ones(X.shape[1]) / initExp['lambda_']),
                 't': 0,
                 'b': [0]*initExp['d'],
                 'participant_uid': args['participant_uid']}
            participant_doc.update(d)
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                         key_value_dict=participant_doc)
        # if not 'theta_star' in participant_doc:
        #     i_star = participant_doc['i_star']
        #     d = {'reward': calc_reward(i_hat, X[:, i_star], R=reward_coeff
        #          * initExp['R']),
        #          'theta_star': (X[:, i_star])}
        #     participant_doc.update(d)
        #     butler.participants.set_many(uid=participant_doc['participant_uid'],
        #                             key_value_dict=participant_doc)            
        if not 'theta_hat' in participant_doc:
            d = {'theta_hat':X[:, participant_doc['i_hat']]}
            participant_doc.update(d)
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                         key_value_dict=participant_doc)
            butler.participants.append(uid=participant_doc['participant_uid'],
                                         key='do_not_ask', value=participant_doc['i_hat'])

        # Figure out what query to ask
        t = participant_doc['t']
        log_div = (1 + t * 1.0/initExp['lambda_']) * 1.0 / initExp['failure_probability']
        k = initExp['R'] * np.sqrt(initExp['d'] * np.log(log_div)) + np.sqrt(initExp['lambda_'])
        invV = np.array(participant_doc['invV'])
        beta = np.array(participant_doc['beta'])

        do_not_ask = butler.participants.get(uid=participant_doc['participant_uid'],
                                             key='do_not_ask')

        theta_hat = np.array(participant_doc['theta_hat'])
        arm_x, i_x = argmax_reward(X, theta_hat, invV, beta,
                                    do_not_ask=do_not_ask, k=k)

        butler.participants.append(uid=participant_doc['participant_uid'],
                                             key='do_not_ask', value=i_x)
        # reward = calc_reward(arm_x, np.array(participant_doc['theta_star']),
        #                      R=reward_coeff * initExp['R'])
        # # allow reward to propograte forward to other functions; it's
        # # used later
        # participant_doc['reward'] = reward

        # for key in participant_doc:
        #     butler.participants.set(uid=participant_doc['participant_uid'],
        #                             key=key, value=participant_doc[key])
        return i_x

    @timeit(fn_name='alg:processAnswer')
    def processAnswer(self, butler, target_id=None,
                      target_reward=None, participant_doc=None):
        """
        reporting back the reward of pulling the arm suggested by getQuery

        Expected input:
          (int) target_index : index of arm pulled
          (int) target_reward : reward of arm pulled

        Expected output (comma separated):
          (boolean) didSucceed : did everything execute correctly
        """
        if target_id is None:
            return True

        args = butler.algorithms.get()
        butler.participants.increment(uid=participant_doc['participant_uid'],key='tx')

        # this makes sure the reward propogates from getQuery to processAnswer
        reward = target_reward

        # theta_star = np.array(participant_doc['theta_star'])
        X = get_feature_vectors(butler) # np.asarray(args['X'], dtype=float)
        b = np.array(participant_doc['b'], dtype=float)
        invV = np.array(participant_doc['invV'], dtype=float)
        beta = np.array(participant_doc['beta'], dtype=float)


        arm_pulled = X[:, target_id]

        u = invV.dot(arm_pulled)

        invV -= np.outer(u, u) / (1 + np.inner(arm_pulled, u))

        beta -= (X.T.dot(u))**2 / (1 + beta[target_id])


        b += reward * arm_pulled
        theta_hat = invV.dot(b)

        # save the results
        d = {'invV': invV,
             'beta': beta,
             'b': b,
             'theta_hat':theta_hat}
        participant_doc.update(d)

        start = time.time()
        butler.participants.set_many(uid=participant_doc['participant_uid'],
                                     key_value_dict=participant_doc)
        print("set_many {}".format(time.time() - start))
        return True

    def getModel(self, butler):
        """
        uses current model to return empirical estimates with uncertainties

        Expected output:
          (list float) mu : list of floats representing the emprirical means
          (list float) prec : list of floats representing the precision values
                              (or standard deviation)
        """
        # TODO: I can't see the results without this
        # (and we also need to change the label name if we want to see results,
        # correct?)
        return 0.5  # mu.tolist(), prec


