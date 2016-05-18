"""
* make mapping, targets to features
* work with Zappos dataset
2. generalize to n users, not 1 user
3. choose initial sampling arm
    * myApp.py getQuery/processAnswer help this
    * V, b, theta_hat need to be stored per user
    * add new key to butler.particpants[i]
* make launching easier

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
def argmax_reward(X, theta, V, do_not_ask=[], k=0):
    r"""
    Loop over all columns of X to solve this equation:

        \widehat{x} = \arg \min_{x \in X} x^T theta + k x^T V^{-1} x
    """
    utils.debug_print("OFUL28: do_not_ask = {}".format(do_not_ask))

    sqrt = np.sqrt
    s = time.time()
    iV = np.linalg.inv(V)
    utils.debug_print("time to invert {} matrix = {}".format(iV.shape, time.time() - s))
    rewards = X.T.dot(theta) + sqrt(k)*sqrt((X * (iV.dot(X))).sum(axis=0))

    mask = np.ones(X.shape[1], dtype=bool)
    mask[do_not_ask] = False
    rewards = rewards[mask]
    return X[:, np.argmax(rewards)], np.argmax(rewards)

@timeit(fn_name="calc_reward")
def calc_reward(x, theta, R=2):
    return np.inner(x, theta) + R*np.random.randn()

@timeit(fn_name="get_feature_vectors")
def get_feature_vectors(butler):
    features = np.load('features.npy')
    utils.debug_print("OFUL 95, features.shape = {}".format(features.shape))
    return features

    # targets = butler.targets.get_targetset(butler.exp_uid, pop=False)
    # utils.debug_print(type(targets))
    # features_vecs = [target['feature_vector'] for target in targets]
    # X = np.array(features_vecs).T
    # utils.debug_print("OFUL:56, X.shape = {}".format(X.shape))
    # return X
    # return butler.targets.features
    # utils.debug_print("oFUL:53, before getting X")
    # n = butler.experiment.get(key='args')['n']
    # X = [butler.targets.get_target_item(butler.exp_uid, i)['feature_vector']
                                            # for i in range(n)]
    # Y = np.array(X).T
    # utils.debug_print("oFUL:58, done getting X")
    # return Y

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
        utils.debug_print("OFUL88: X.shape = {}".format(X.shape))
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

        if not 'V' in participant_doc.keys():
            # * V, b, theta_hat need to be stored per user

            d = {'V': (initExp['lambda_'] * np.eye(initExp['d'])).tolist(),
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
        #          'theta_star': (X[:, i_star]).tolist()}
        #     participant_doc.update(d)
        #     butler.participants.set_many(uid=participant_doc['participant_uid'],
        #                             key_value_dict=participant_doc)            
        if not 'theta_hat' in participant_doc:
            d = {'theta_hat':X[:, participant_doc['i_hat']].tolist(),}
            participant_doc.update(d)
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                         key_value_dict=participant_doc)
            butler.participants.append(uid=participant_doc['participant_uid'],
                                         key='do_not_ask', value=participant_doc['i_hat'])

        # Figure out what query to ask
        t = participant_doc['t']
        log_div = (1 + t * 1.0/initExp['lambda_']) * 1.0 / initExp['failure_probability']
        k = initExp['R'] * np.sqrt(initExp['d'] * np.log(log_div)) + np.sqrt(initExp['lambda_'])
        V = np.array(participant_doc['V'])

        do_not_ask = butler.participants.get(uid=participant_doc['participant_uid'],
                                             key='do_not_ask')

        arm_x, i_x = argmax_reward(X, np.array(participant_doc['theta_hat']),
                                   V, do_not_ask=do_not_ask, k=k)

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
        utils.debug_print("OFUL:193:processAnswer, reward = {}".format(reward))

        # theta_star = np.array(participant_doc['theta_star'])
        X = get_feature_vectors(butler) # np.asarray(args['X'], dtype=float)
        b = np.array(participant_doc['b'], dtype=float)
        V = np.array(participant_doc['V'], dtype=float)

        arm_pulled = X[:, target_id]

        V += np.outer(arm_pulled, arm_pulled)
        b += reward * arm_pulled
        theta_hat = np.linalg.inv(V).dot(b)

        # save the results
        d = {'V': V.tolist(),
             'b': b.tolist(),
             'theta_hat':theta_hat.tolist()}
        participant_doc.update(d)

        butler.participants.set_many(uid=participant_doc['participant_uid'],
                                     key_value_dict=participant_doc)
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


