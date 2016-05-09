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
reward_coeff = 0.01

def argmax_reward(X, theta, V, k=0):
    r"""
    Loop over all columns of X to solve this equation:

        \widehat{x} = \arg \min_{x \in X} x^T theta + k x^T V^{-1} x
    """
    inv = np.linalg.inv
    norm = np.linalg.norm
    rewards = [np.inner(X[:, c], theta) + k*np.inner(X[:, c], inv(V).dot(X[:, c]))
               for c in range(X.shape[1])]
    rewards = np.asarray(rewards)
    return X[:, np.argmax(rewards)], np.argmax(rewards)

def calc_reward(x, theta, R=2):
    return np.inner(x, theta) + R*np.random.randn()

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
        X = np.asarray(params['X'])
        utils.debug_print(X.shape)
        theta_star = np.asarray(params['theta_star'])

        d = X.shape[0]  # number of dimensions in feature
        lambda_ = 1.0 / d
        # V = lambda_ * np.eye(d)
        R = 2.0

        # initial sampling arm
        # theta_hat = X[:, np.random.randint(X.shape[1])]
        # theta_hat = np.random.randn(d)
        # theta_hat /= np.linalg.norm(theta_hat)

        to_save = {'X': X.tolist(),
                   'R': R, 'd': d, 'n': n,
                   # 'theta_hat': theta_hat.tolist(),
                   # 'theta_star': theta_star.tolist(),
                   # 'V': V.tolist(),
                   'lambda_': lambda_,
                   'total_pulls': 0.0,
                   'rewards': [],
                   'arms_pulled': [],
                   # 'b': [0]*d,
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
        X = np.asarray(initExp['X'], dtype=float)
        butler.algorithms.increment(key='total_pulls')
        t = butler.algorithms.get(key='total_pulls')

        # this is the initial sampling state
        # TODO: make this use total_pulls
        if not 'num_tries' in participant_doc.keys():
            participant_doc['num_tries'] = 0
            # * V, b, theta_hat need to be stored per user
            # np.random.seed(int(time.time() * 100) % 2**10)

            i_hat = np.random.randint(X.shape[1])

            d = {'num_tries': 0,
                 'theta_hat': X[:, i_hat].tolist(),
                 'V': (initExp['lambda_'] * np.eye(initExp['d'])).tolist(),
                 'b': [0]*initExp['d'],
                 'participant_uid': args['participant_uid']
                 }
            participant_doc.update(d)
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                    key_value_dict=participant_doc)
            return None
        elif participant_doc['num_tries'] == 0:
            i_star = participant_doc['i_star']
            d = {'reward': calc_reward(i_hat, X[:, i_star], R=reward_coeff
                 * initExp['R']),
                 'theta_star': X[:, i_star].tolist()}
            participant_doc.update(d)
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                    key_value_dict=participant_doc)            

        log_div = (1 + t * 1.0/initExp['lambda_']) * 1.0 / initExp['failure_probability']
        k = initExp['R'] * np.sqrt(initExp['d'] * np.log(log_div)) + np.sqrt(initExp['lambda_'])

        # arm_x = X[:, i_x]
        V = np.array(participant_doc['V'])
        arm_x, i_x = argmax_reward(X, np.array(participant_doc['theta_hat']),
                                   V, k=k)


        reward = calc_reward(arm_x, np.array(participant_doc['theta_star']),
                             R=reward_coeff * initExp['R'])
        # allow reward to propograte forward to other functions; it's used
        # later
        participant_doc['reward'] = reward

        for key in participant_doc:
            butler.participants.set(uid=participant_doc['participant_uid'],
                                    key=key, value=participant_doc[key])
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
        args = butler.algorithms.get()
        utils.debug_print('OFUL168')
        utils.debug_print(participant_doc.keys())

        # this makes sure the reward propogates from getQuery to processAnswer
        reward = participant_doc['reward']

        X = np.asarray(args['X'], dtype=float)
        b = np.array(participant_doc['b'], dtype=float)
        theta_star = np.array(participant_doc['theta_star'])

        V = np.array(participant_doc['V'])
        arm_pulled = X[:, target_id]

        V += np.outer(arm_pulled, arm_pulled)
        b += reward * arm_pulled
        theta_hat = np.linalg.inv(V).dot(b)

        utils.debug_print("OFUL:131, ||theta_star - theta_hat||_2 = {}"
                    .format(np.linalg.norm(theta_star - theta_hat)))

        # save the results
        d = {'V': V.tolist(),
             'b':b.tolist(),
             'theta_hat':theta_hat.tolist()}
        participant_doc.update(d)

        for key in participant_doc:
            butler.participants.set(uid=participant_doc['participant_uid'],
                                    key=key, value=participant_doc[key])
        for name, value in [('X', X)]:
            butler.algorithms.set(key=name, value=value)
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


