"""
Utility functions for the api. This includes generation of meta and error messages. 
All overrided classes and methods of Flask should go here.

Author: Lalit Jain, lalitkumarj@gmail.com 
"""

import time

def timeit(f):
    """ 
    Utility used to time the duration of code execution. This script can be composed with any other script.
    
    Usage::\n
      def f(n): 
        return n**n  

      def g(n): 
        return n,n**n 

      answer0,dt = timeit(f)(3)
      answer1,answer2,dt = timeit(g)(3)
    """
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        if type(result)==tuple:
            return result + ((te-ts),)
        else:
            return result,(te-ts)
    return timed


def attach_meta(response, meta, **kwargs):
    """
    Attach a meta dictionary to a response dictionary.
 
    Inputs: :\n
    	(dict) response, (dict) meta, (key-value pairs) kwargs - optional messages to add to mets

    Usage: :\n
    """
    for k,v in kwargs.iteritems():
        meta[k] = v
        
    response["meta"] = meta
    return response

verification_error = {
    'message':'Failed to Authenticate',
    'status':'FAIL',
    'code':401
    }


from flask.ext.restful import Api
import sys, traceback
class NextBackendApi(Api):
    """
    Subclass of the default Api class of Flask-Restful with custom error handling for 500 requests
    
    All other errors are passed onto the default handle_error.
    """
    def handle_error(self, e, **kwargs):
        exc_type, exc_value, tb = sys.exc_info()
        backend_error = traceback.format_exc(tb)            
        print "backend_error", backend_error,exc_type, exc_value, tb, traceback.format_exc(tb)

        # Catch internal system errors
        code = getattr(e, 'code', 500)
        if code == 500:      
            response = {
                'meta':{
                    'status': 'FAIL',
                    'code': 500,
                    'message': 'Internal Server Error',
                    'backend_error': backend_error
                }
            }
            return self.make_response(response, 500)        
    	return super(NextBackendApi, self).handle_error(e) 



from flask.ext.restful.reqparse import RequestParser
from flask.ext.restful.reqparse import Argument
from flask.ext.restful.reqparse import Namespace
from flask.ext.restful import abort

class APIArgument(Argument):
    """
    Subclass of the standard flask restful Argument class to provide a custom meta message.
    Passes up a 400 message if arguments are not correctly parsed.
    """
    def __init__(self, *args, **kwargs):
        """
        Pass up the default arguments. 
        """
        super(APIArgument, self).__init__(*args, **kwargs)
    
    def handle_validation_error(self, error, bundle_errors):
        """
        Called when an error is raised while parsing. Aborts the request
        with a 400 status and a meta error dictionary.

        Can I do this through the exception handling system?

        :param error: the error that was raised
        """
        help_str = '(%s) ' % self.help if self.help else ''
        msg = '[%s]: %s%s' % (self.name, help_str, str(error))
        if bundle_errors:
            return error, msg
        return abort(400, meta={'message':msg, 'code':400, 'status':'FAIL'})


# Custom Exception types for the api. These should just pass.
class DatabaseException(Exception):
    pass

class BackendConnectionException(Exception):
    pass
