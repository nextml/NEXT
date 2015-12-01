#!/usr/bin/python
import test_api_bad_inputs
import test_conn

'''
A common design pattern for open source machine learning projects involves:
	- Training a system/model with data that yeilds known, expected outputs
	- Testing a system/model by verifying that the known, expected outputs are predicted

See vowpal_wabbit, scikit-learn, and bigml for examples:
	- https://github.com/JohnLangford/vowpal_wabbit/tree/master/test
	- https://github.com/scikit-learn/scikit-learn/tree/master/sklearn/tests
	- https://github.com/bigmlcom/python/tree/next/bigml/tests

In active learning, the system/model plays an interactive role in generating these data.
Thus, it is not necessarily practical to expect specific outputs to data that are generated adaptively.

As such, the scope of this testing suite is to ensure proper functionality of all application and algorithm APIs.
Verification that individual algorithms and applications actually work well is more subtle, and should be evaluated carefully by other means.

This run_all_tests.py file executes the test_api_*.py file for each application type.
Each application type should have an associated test that:
	- Implements and executes all API calls, creating and running multiple experiments from 'start-to-finish'
	- Simulates user input data in the form of getQuery and processAnswer API calls
	- Verifies that that all API requests and responses are proccessed correctly (e.g. status codes or other means)
'''

if __name__ == '__main__':
	assert_200 = False
	num_clients = 1
	# test_conn.run_all()
	# test_api_bad_inputs.run_all(assert_200, num_clients)
	# test_api_dueling.run_all(assert_200)
	# test_api_triplet.run_all(assert_200, num_clients)
	# test_api_tuple.run_all(assert_200)
	# add subsequent tests here
