"""
This file is to provide a unifed testing framework for NEXT.
"""
from __future__ import print_function
import requests
import os
import json
import time
import numpy as np

HOSTNAME = (
    os.environ.get("NEXT_BACKEND_GLOBAL_HOST", "localhost")
    + ":"
    + os.environ.get("NEXT_BACKEND_GLOBAL_PORT", "8000")
)


def initExp(initExp_args_dict, assert_200=True):
    url = "http://" + HOSTNAME + "/api/experiment"
    response = requests.post(
        url, json.dumps(initExp_args_dict), headers={"content-type": "application/json"}
    )
    print("POST initExp response =", response.text, response.status_code)
    if assert_200:
        assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)

    exp_uid = initExp_response_dict["exp_uid"]

    #################################################
    # Test initExperiment
    #################################################
    url = "http://" + HOSTNAME + "/api/experiment/" + exp_uid
    response = requests.get(url)
    print("GET experiment response =", response.text, response.status_code)
    if assert_200:
        assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)
    return initExp_response_dict, {"exp_uid": exp_uid}


def getQuery(getQuery_args_dict, assert_200=True, verbose=False):
    url = "http://" + HOSTNAME + "/api/experiment/getQuery"
    response, dt = timeit(requests.post)(
        url,
        json.dumps(getQuery_args_dict),
        headers={"content-type": "application/json"},
    )
    if verbose:
        print("POST getQuery response = ", response.text, response.status_code)
    if assert_200:
        assert response.status_code is 200

    if verbose:
        print("POST getQuery duration = ", dt)
    query_dict = json.loads(response.text)
    return query_dict, dt


def processAnswer(processAnswer_args_dict, assert_200=True, verbose=False):
    url = "http://" + HOSTNAME + "/api/experiment/processAnswer"
    if verbose:
        print("POST processAnswer args = ", processAnswer_args_dict)
    response, dt = timeit(requests.post)(
        url,
        json.dumps(processAnswer_args_dict),
        headers={"content-type": "application/json"},
    )
    if verbose:
        print("POST processAnswer response", response.text, response.status_code)
    if assert_200:
        assert response.status_code is 200

    if verbose:
        print("POST processAnswer duration = ", dt)
        print()
    processAnswer_json_response = eval(response.text)
    return processAnswer_json_response, dt


def timeit(f):
    """
    Refer to next.utils.timeit for further documentation
    """

    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        if type(result) == tuple:
            return result + ((te - ts),)
        else:
            return result, (te - ts)

    return timed


def getModel(exp_uid, app_id, supported_alg_ids, alg_list, assert_200=True):
    # Test loading the dashboard
    dashboard_url = (
        "http://" + HOSTNAME + "/dashboard"
        "/experiment_dashboard/{}/{}".format(exp_uid, app_id)
    )
    response = requests.get(dashboard_url)
    if assert_200:
        assert response.status_code is 200

    stats_url = "http://" + HOSTNAME + "/dashboard" "/get_stats".format(exp_uid, app_id)

    args = {"exp_uid": exp_uid, "args": {"params": {"alg_label": supported_alg_ids[0]}}}
    args = {"exp_uid": exp_uid, "args": {"params": {}}}
    alg_label = alg_list[0]["alg_label"]
    params = {
        "api_activity_histogram": {},
        "compute_duration_multiline_plot": {"task": "getQuery"},
        "compute_duration_detailed_stacked_area_plot": {
            "alg_label": alg_label,
            "task": "getQuery",
        },
        "response_time_histogram": {"alg_label": alg_label},
        "network_delay_histogram": {"alg_label": alg_label},
    }
    for stat_id in [
        "api_activity_histogram",
        "compute_duration_multiline_plot",
        "compute_duration_detailed_stacked_area_plot",
        "response_time_histogram",
        "network_delay_histogram",
    ]:
        args["args"]["params"] = params[stat_id]
        args["args"]["stat_id"] = stat_id
        response = requests.post(stats_url, json=args)
        if assert_200:
            assert response.status_code is 200


def getExp(exp_uid, assert_200=True):
    url = "http://" + HOSTNAME + "/api/experiment/" + exp_uid
    response = requests.get(url)
    print("GET experiment response =", response.text, response.status_code)
    if assert_200:
        assert response.status_code is 200
    initExp_response_dict = json.loads(response.text)
    return initExp_response_dict


def format_times(getQuery_times, processAnswer_times, total_pulls, participant_uid):
    processAnswer_times.sort()
    getQuery_times.sort()
    return_str = (
        "%s \n\t getQuery\t : %f (5),        %f (50),        %f (95)\n\t processAnswer\t : %f (5),        %f (50),        %f (95)\n"
        % (
            participant_uid,
            getQuery_times[int(.05 * total_pulls)],
            getQuery_times[int(.50 * total_pulls)],
            getQuery_times[int(.95 * total_pulls)],
            processAnswer_times[int(.05 * total_pulls)],
            processAnswer_times[int(.50 * total_pulls)],
            processAnswer_times[int(.95 * total_pulls)],
        )
    )
    return return_str


def response_delay(std=0.05, mean=0.1):
    ts = time.time()
    sleep_time = np.abs(np.random.randn() * std + mean)
    time.sleep(sleep_time)
    return ts
