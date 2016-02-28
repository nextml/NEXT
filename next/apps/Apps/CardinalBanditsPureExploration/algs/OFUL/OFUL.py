import numpy as np
from next.apps.Apps.CardinalBanditsPureExploration.Prototype import CardinalBanditsPureExplorationPrototype


class OFUL(CardinalBanditsPureExplorationPrototype):

    def initExp(self, butler, n, R, failure_probability, params):
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
        # Is there a conflict here? `params` should be a dictionary containing
        # algorithm specific parameters. Or, I should hard code them in here
        ridge = 0.2

        # setting the target matrix, a description of each target
        X = np.asarray(params)
        d = len(X[:, 0])  # number of dimensions in feature
        butler.algorithms.set(key='X', value=X)

        num_tries = butler.algorithms.get(key='num_tries')
        num_tries = 2  # TODO: this should be default! change it
        print "OFUL:32 ", num_tries
        #num_tries = 3
        butler.algorithms.set(key='n', value=n)
        butler.algorithms.set(key='d', value=d)
        butler.algorithms.set(key='R', value=R)

        # this is delta in oful_caf.m
        butler.algorithms.set(key='failure_probability', value=failure_probability)
        butler.algorithms.set(key='ridge'       , value=ridge)
        butler.algorithms.set(key='valid_inds'  , value=range(n))

        # T == num_tries \approx 25 and is managed for us by App.py
        butler.algorithms.set(key='reward'      , value=np.zeros(num_tries))
        butler.algorithms.set(key='arms_pulled' , value=np.zeros(num_tries))
        butler.algorithms.set(key='invVt'       , value=np.eye(d) / failure_probability)
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

        # X is precomputed and stored somewhere. Stored as a .mat file
        # (look for something with feature_normalized)
        beta = np.zeros(num_tries)
        for i in range(num_tries):
            beta[i] = X[:, i].T.dot(X[:, i]) / ridge

        # TODO: check to see if saving array to database works
        butler.algorithms.set(key='beta', value=beta)

        return True

    def getQuery(self, butler, do_not_ask_list):
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

        # X0 is the initial sampling arm
        if args['total_pulls'] == 0:
            return np.random.randint(0, args['n'])
            #X[:, i] # return the feature id, not the feature
        butler.algorithms.increment(key='total_pulls')

        # TODO: there's a dependency on t or total questions asked
        Kt = args['R'] * sqrt(args['d'] * log((1 + t/args['ridge'])/args['delta']))
        term1 = Kt * np.sqrt(args['beta'])
        term2 = theta_T.T.dot(X)

        # Possible bug: is this list concat or actual addition?
        max_index = np.argmax(term1[valid_inds] + term2[valid_inds])
        max_index = valid_inds[max_index]
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
        X = np.asarray(args['X'])

        args['b_' + str(target_id)] += target_reward * X[:, target_id]

        val = args['invVt'].dot(X[:, target_id])
        var2 = X[:, target_id].T.dot(val)
        beta -= ((X.T.dot(val))**2).T / (1 + val2)
        invVt -= (val.dot(val.T)) / (1 + val2)
        theta_t = invVt.dot(b)
        valid_inds = list(set(valid_inds) - set(arms_pulled[t]))
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
        return 0.5 #mu.tolist(), prec


