from next.api import api_blueprint
from next.dashboard import dashboard
from next.query_page import query_page

from flask import Flask
app = Flask(__name__)
app.register_blueprint(api_blueprint.api, url_prefix='/api')
app.register_blueprint(dashboard, url_prefix='/dashboard')
app.register_blueprint(query_page, url_prefix='/query')

import logging
import sys
# Log to standard out. Remember to turn off in production
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

#Handle internal errors using a custom error message
import json
@app.errorhandler(404)
def internal_system_error(error):
    response  = {
        'meta':{
            'status':'FAIL',
            'code':404,
            'message':'Resource not found'
        }
    }
    return json.dumps(response), 404
                  
