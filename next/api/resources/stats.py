"""
next_backend Statistics Resource 
author: Christopher Fernandez, Lalit Jain
Stats resource for handling restful communication with next_backend analytics dashboards. 
"""
'''
example use:

get a tripletMDS stats:
curl -H "Content-Type: application/json" \
-d '{"exp_uid": "DFPDISJFSA", "app_id": "PoolBasedTripletMDS", "args":{ "stat_id": "api_activity_histogram", "params": { "task": "getQuery"}}}' \
-X POST http://localhost:8001/experiment/stats
'''
from flask import Flask, Response, make_response
from flask.ext import restful
from flask.ext.restful import Resource, reqparse

import json
import time
from cStringIO import StringIO
import gzip
import next.utils
import next.broker.broker
from next.api.api_util import *
from next.api.api_util import APIArgument

from next.api.targetmapper import TargetMapper
from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
targetmapper = TargetMapper() 
keychain = KeyChain()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed. 
post_parser = reqparse.RequestParser(argument_class=APIArgument)

# Custom errors for GET and POST verbs on experiment resource
meta_error = {
    'StatsRetrievalError': {
        'message': "Error: Stats could not be retrieved.",
        'code': 400,
        'status': 'FAIL'
    },
    'StatsEmptyError': {
        'message': "No stats can be retrieved for the specified experiment.",
        'code': 200,
        'status': 'OK'
    }
}

meta_success = {
    'status':'OK',
    'code':200
    }

class Stats(Resource):

    def options(self):
        return None, 200, {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'}
  
    def post(self):
        """
        .. http:post:: /experiment/stats

        Get stats related to an experiment. For a list of potential plot types and parameters see: LINK.

        **Example request**:
        .. sourcecode:: http

        POST /experiment/<exp_uid> HTTP/1.1
        Host: next_backend.next.discovery.wisc.edu

        {
	        exp_uid: exp_uid,
        	args: {
                stat_id: "compute_duration_detailed_stacked_area_plot",
                params: {
                          task: "getQuery",
                          alg_label: "lilUCB"
                }        
            }
        }

        **Example response**:

        .. sourcecode:: http
        
        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
        	
        	plot_type: 'multi_line_plot'
          	x_label : 'Number of answered triplets'
          	x_min : 1
          	x_max : maximum number of reported answers for any algorithm
          	y_label : 'Error on hold-out set'
          	y_min : 0.
          	y_max : maximum duration value achieved by any algorithm
        	data :[ 
            		t : list of timestamp strings
           		x : integers ranging from 1 to maximum number of elements in y (or t)
            		y : list of durations
            		legend_label : alg_label
		]    
        }

        
        :statuscode 200: stats successfully accessed
        :statuscode 400: stats retrieval error
        """        
        post_parser.add_argument('exp_uid', type=str, required=True)
        post_parser.add_argument('exp_key', type=str, required=True)
        post_parser.add_argument('args', type=dict, required=True)

        # Validate args with post_parser
        args_data = post_parser.parse_args()

        # Pull app_id and exp_uid from parsed args_data
        exp_uid = args_data["exp_uid"]
        exp_key = args_data["exp_key"]
        if not keychain.verify_exp_key(exp_uid, exp_key):
            return api_util.attach_meta({}, api_util.verification_dictionary), 401

        # Fetch app_id data from resource manager
        app_id = resource_manager.get_app_id(exp_uid)

        # Args from dict to json type
        args_json = json.dumps(args_data["args"])

        # Execute getStats
        response_json,didSucceed,message = broker.applyAsync(app_id,exp_uid,"getStats",args_json)
        response_dict = json.loads(response_json,parse_float=lambda o:round(float(o),4))

        try:
            index_test = response_dict['data'][0]['index']
            targetmapping = targetmapper.get_target_mapping(exp_uid)
            for d in response_dict['data']:
                try:
                    index = d['index']
                    if len(targetmapping)==0:
                        d['target'] = {'target_id':index,
                                        'primary_description':index,
                                        'primary_type':'text',
                                        'alt_description':index,
                                        'alt_type':'text'}
                    else:
                        d['target'] = targetmapping[index]
                except:
                    pass
        except:
            pass
        
        if didSucceed and "data" in response_dict.keys():
            t = time.time()
            json_response = json.dumps(attach_meta(response_dict,meta_success)) 
            gzip_buffer = StringIO()
            gzip_file = gzip.GzipFile(mode='wb', 
                                      fileobj=gzip_buffer)
            gzip_file.write(json_response)
            gzip_file.close()
            resp = make_response(gzip_buffer.getvalue())
            print "time to zip", time.time() - t
            resp.headers['Content-Encoding']='gzip'
            resp.headers['Content-length']=len(json.dumps(attach_meta(response_dict,meta_success)))
            resp.headers['Content-Type'] = 'application/json'
            return resp
            # return gzip_buffer.getvalue(), 200, {'Content-Encoding': 'gzip',
            #                                      'Vary':'Accept-Encoding',
            #                                      'Content-Type': 'application/json'}
        elif didSucceed and not "data" in response_dict.keys():
            return attach_meta({'data':[]},meta_error['StatsEmptyError']), 200
        else:
            return attach_meta({},meta_error['StatsRetrievalError'], backend_error=message), 400

