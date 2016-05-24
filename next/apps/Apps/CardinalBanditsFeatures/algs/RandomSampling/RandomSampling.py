from __future__ import division
import numpy as np
from next.apps.Apps.CardinalBanditsFeatures.Prototype import CardinalBanditsFeaturesPrototype
import next.utils as utils
import time

# TODO: change this to 1
reward_coeff = 1.00

class RandomSampling(CardinalBanditsFeaturesPrototype):
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
        butler.algorithms.set(key='n', value=n)
        utils.debug_print("random:28, n = {}".format(n))
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
        if not 'num_tries' in participant_doc.keys():
            participant_doc['participant_uid'] = args['participant_uid']
            participant_doc['num_tries'] = 0
            participant_doc['do_not_ask'] = []
            butler.participants.set_many(uid=participant_doc['participant_uid'],
                                         key_value_dict=participant_doc)
            return None

        n = butler.algorithms.get(key='n')
        return np.random.randint(n)

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


