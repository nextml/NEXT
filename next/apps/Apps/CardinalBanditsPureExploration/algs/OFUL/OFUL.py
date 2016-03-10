import numpy as np
from next.apps.Apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype
import next.utils as utils

class OFUL(CardinalBanditsPureExplorationPrototype):

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

        utils.debug_print("OFUL.py:29, n = {}".format(n))
        utils.debug_print("OFUL.py:29, R = {}".format(R))
        utils.debug_print("After removing timeit")
        # Is there a conflict here? `params` should be a dictionary containing
        # algorithm specific parameters. Or, I should hard code them in here
        ridge = 0.2

        # setting the target matrix, a description of each target
        X = np.asarray(params)
        d = len(X[:, 0])  # number of dimensions in feature

        # We're saving params as a list of lists, not a ndarray
        butler.algorithms.set(key='X', value=params)

        # num_tries = butler.experiment.get(key='num_tries')
        num_tries = 2  # TODO: this should be default! change it
        # it should be butler.experiment.get(key='num_tries') but I don't have
        # time to test it right now

        # num_tries = 3
        butler.algorithms.set(key='n', value=n)
        butler.algorithms.set(key='d', value=d)
        butler.algorithms.set(key='R', value=R)

        # this is delta in oful_caf.m
        butler.algorithms.set(key='failure_probability',
                              value=failure_probability)
        butler.algorithms.set(key='ridge', value=ridge)
        butler.algorithms.set(key='valid_inds', value=range(n))

        # T == num_tries \approx 25 and is managed for us by App.py
        reward = np.zeros(num_tries)
        arms_pulled = np.zeros(n)
        invVt = np.eye(d) / failure_probability

        butler.algorithms.set(key='reward'      , value=reward.tolist())
        butler.algorithms.set(key='arms_pulled' , value=arms_pulled.tolist())
        butler.algorithms.set(key='invVt'       , value=invVt.tolist())
        butler.algorithms.set(key='S_hat'       , value=1.0)
        butler.algorithms.set(key='total_pulls' , value=0.0)

        # I assume Xsum_i and X2sum_i are the reward for each arm
        # I don't know what T_i is
        arm_key_value_dict = {}
        for i in range(n):
            arm_key_value_dict['Xsum_' + str(i)] = 0.
            arm_key_value_dict['T_' + str(i)] = 0.

        # b stores a linear combo of the arms
        for i in range(d):
            arm_key_value_dict['b_' + str(i)] = 0.

        arm_key_value_dict.update({'total_pulls':0,'generated_queries_cnt':-1})
        butler.algorithms.increment_many(key_value_dict=arm_key_value_dict)
        butler.algorithms.set(key='b', value=np.zeros(d).tolist())

        beta = np.zeros(n)
        for i in range(n):
            beta[i] = X[:, i].T.dot(X[:, i]) / ridge

        butler.algorithms.set(key='beta', value=beta.tolist())

        # This is the initial sampling arm (of features!)
        initial_sampling = X[:, np.random.randint(n)]
        butler.algorithms.set(key='theta_T', value=initial_sampling.tolist())

        return True

    def getQuery(self, butler, do_not_ask_list, exp_uid=None, args=None):
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
        """
        args = butler.algorithms.get()
        X = np.asarray(args['X'])

        butler.algorithms.increment(key='total_pulls')
        t = butler.algorithms.get(key='total_pulls')

        Kt = args['R'] * np.sqrt(args['d'] * np.log((1 + t/args['ridge'])/args['failure_probability']))

        # theta_T: the arm to pull; this should be updated each iteration,
        # right?  yes, they are updated each iteration in processAnswer
        theta_T = butler.algorithms.get(key='theta_T')
        theta_T = np.asarray(theta_T)

        term1 = Kt * np.sqrt(args['beta'])
        term2 = theta_T.T.dot(X)

        utils.debug_print("OFUL.py:126, type(theta_T) = {}, theta_T = {}".format(type(theta_T), theta_T))
        utils.debug_print("OFUL.py:127 X.shape {}".format((X[:, 1].T.dot(X)).shape))
        utils.debug_print("OFUL.py:127 term.shape {} {}".format(term1.shape, term2.shape))

        max_index = np.argmax(term1[args['valid_inds']] + term2[args['valid_inds']])
        max_index = args['valid_inds'][max_index]
        arms_pulled = butler.algorithms.get(key='arms_pulled')
        arms_pulled[max_index] += 1
        butler.algorithms.set(key='arms_pulled', value=arms_pulled)

        return max_index

    def processAnswer(self, butler, target_id, target_reward):
        """
        reporting back the reward of pulling the arm suggested by getQuery

        Expected input:
          (int) target_index : index of arm pulled
          (int) target_reward : reward of arm pulled

        Expected output (comma separated):
          (boolean) didSucceed : did everything execute correctly
        """
        args = butler.algorithms.get()
        t = butler.algorithms.get(key='total_pulls')
        arms_pulled = butler.algorithms.get(key='arms_pulled')
        X = np.asarray(args['X'])

        args['b'] += target_reward * X[:, target_id]

        val = np.asarray(args['invVt']).dot(X[:, target_id])
        val2 = X[:, target_id].T.dot(val)

        # I have verified that this is an element-wise power
        args['beta'] -= ((X.T.dot(val))**2).T / (1 + val2)
        args['invVt'] -= (val.dot(val.T)) / (1 + val2)
        theta_T = args['invVt'].dot(args['b'])

        butler.algorithms.set(key='theta_T', value=theta_T.tolist())

        inds = np.array(args['valid_inds'], dtype=int)
        # TODO: return args['valid_inds'] or store in some way
        args['valid_inds'] = set(inds) - set([arms_pulled[int(t)]])
        args['valid_inds'] = list(args['valid_inds'])
        # TODO: store S_hat somewhere
        S_hat = 1
        return True

    def getModel(self, butler):
        """
        uses current model to return empirical estimates with uncertainties

        Expected output:
          (list float) mu : list of floats representing the emprirical means
          (list float) prec : list of floats representing the precision values
                              (or standard deviation)
        """
        return 0.5  # mu.tolist(), prec


