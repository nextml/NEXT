from __future__ import print_function
import numpy
import numpy as np
import numpy.random
import random
import json
import time
from datetime import datetime
import requests
from scipy.linalg import norm
import time
from multiprocessing import Pool
import sys
import os

try:
    import next.apps.test_utils as test_utils
except:
    file_dir = "/".join(__file__.split("/")[:-1])
    sys.path.append("{}/../../../next/apps".format(file_dir))
    import test_utils


def test_api(
    assert_200=True, num_arms=5, num_experiments=1, num_clients=10, total_pulls=10
):
    app_id = "CardinalBanditsPureExploration"
    true_means = numpy.array(range(num_arms)[::-1]) / float(num_arms)

    pool = Pool(processes=min(100, num_clients))

    # input test parameters
    n = num_arms
    delta = 0.05
    supported_alg_ids = ["LilUCB", "KLUCB", "RoundRobin"]

    labels = [
        {"label": "bad", "reward": 1.},
        {"label": "neutral", "reward": 2.},
        {"label": "good", "reward": 3.},
    ]

    alg_list = []
    for i, alg_id in enumerate(supported_alg_ids):
        alg_item = {}
        alg_item["alg_id"] = alg_id
        alg_item["alg_label"] = alg_id + "_" + str(i)
        # alg_item['params'] = {}
        alg_list.append(alg_item)
    params = []
    # params['proportions'] = []
    for algorithm in alg_list:
        params.append(
            {"alg_label": algorithm["alg_label"], "proportion": 1. / len(alg_list)}
        )
    algorithm_management_settings = {}
    algorithm_management_settings["mode"] = "fixed_proportions"
    algorithm_management_settings["params"] = params

    print("alg mangement settings", algorithm_management_settings)

    # Test POST Experiment
    initExp_args_dict = {}
    initExp_args_dict["args"] = {}

    initExp_args_dict["args"]["targets"] = {"n": n}
    initExp_args_dict["args"]["failure_probability"] = delta
    initExp_args_dict["args"][
        "participant_to_algorithm_management"
    ] = "one_to_many"  # 'one_to_one'    #optional field
    initExp_args_dict["args"][
        "algorithm_management_settings"
    ] = algorithm_management_settings  # optional field
    initExp_args_dict["args"]["alg_list"] = alg_list  # optional field
    initExp_args_dict["args"][
        "instructions"
    ] = "You want instructions, here are your test instructions"
    initExp_args_dict["args"][
        "debrief"
    ] = "You want a debrief, here is your test debrief"
    initExp_args_dict["args"]["context_type"] = "text"
    initExp_args_dict["args"]["context"] = "This is a context"
    initExp_args_dict["args"]["rating_scale"] = {"labels": labels}
    #    initExp_args_dict['args']['HAHA'] = {'labels':labels}
    initExp_args_dict["app_id"] = app_id

    exp_info = []
    print("Initializing experiment...")
    for ell in range(num_experiments):
        initExp_response_dict, exp_uid = test_utils.initExp(initExp_args_dict)
        exp_info += [exp_uid]

        exp_uid = initExp_response_dict["exp_uid"]
        exp_info += [{"exp_uid": exp_uid}]

        # Test GET Experiment
        initExp_response_dict = test_utils.getExp(exp_uid)
    print("...done")

    # Generate participants
    participants = []
    pool_args = []
    for i in range(num_clients):
        participant_uid = "%030x" % random.randrange(16 ** 30)
        participants.append(participant_uid)

        experiment = numpy.random.choice(exp_info)
        exp_uid = experiment["exp_uid"]
        pool_args.append(
            (exp_uid, participant_uid, total_pulls, true_means, assert_200)
        )

    print("Participants are responding")
    results = pool.map(simulate_one_client, pool_args)

    for result in results:
        result

    test_utils.getModel(exp_uid, app_id, supported_alg_ids, alg_list)


def simulate_one_client(input_args):
    exp_uid, participant_uid, total_pulls, true_means, assert_200 = input_args
    verbose = False

    test_utils.response_delay()

    getQuery_times = []
    processAnswer_times = []

    for t in range(total_pulls):
        print("Participant {} has had {} pulls".format(participant_uid, t))

        # test POST getQuery #
        getQuery_args_dict = {}
        getQuery_args_dict["exp_uid"] = exp_uid
        getQuery_args_dict["args"] = {}
        # getQuery_args_dict['args']['participant_uid'] = numpy.random.choice(participants)
        getQuery_args_dict["args"]["participant_uid"] = participant_uid

        query_dict, dt = test_utils.getQuery(getQuery_args_dict)
        getQuery_times += [dt]

        query_uid = query_dict["query_uid"]
        targets = query_dict["target_indices"]
        target_index = targets[0]["target"]["target_id"]

        # generate simulated reward #
        # sleep for a bit to simulate response time
        ts = test_utils.response_delay()
        target_reward = 1. + sum(
            numpy.random.rand(2) < true_means[target_index]
        )  # in {1,2,3}
        # target_reward = numpy.random.choice(labels)['reward']
        response_time = time.time() - ts

        # test POST processAnswer
        processAnswer_args_dict = {}
        processAnswer_args_dict["exp_uid"] = exp_uid
        processAnswer_args_dict["args"] = {}
        processAnswer_args_dict["args"]["query_uid"] = query_uid
        target_reward = (
            str(target_reward) if np.random.randint(2) == 0 else target_reward
        )
        processAnswer_args_dict["args"]["target_reward"] = str(target_reward)
        processAnswer_args_dict["args"]["response_time"] = response_time

        processAnswer_json_response, dt = test_utils.processAnswer(
            processAnswer_args_dict
        )
        processAnswer_times += [dt]

    t = test_utils.format_times(
        getQuery_times, processAnswer_times, total_pulls, participant_uid
    )
    return t


if __name__ == "__main__":
    test_api()
    #  test_api(assert_200=True, num_arms=50, total_pulls_per_client=100,
    #  num_experiments=1, num_clients=100, total_pulls=10000)
