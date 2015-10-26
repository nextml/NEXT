import os

from flask import Blueprint, render_template, flash, request, redirect, url_for

import next.constants as constants
from next.api.keychain import KeyChain
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
keychain = KeyChain()
query_page = Blueprint('query_page',
                       __name__,
                       template_folder='templates',
                       static_folder='static')

@query_page.route('/query_page/<page>')
@query_page.route('/query_page/<page>/<exp_uid>/<widget_key>')
def load_page(page, exp_uid=None, widget_key=None):
    experiment = resource_manager.get_experiment(exp_uid)
    num_tries = experiment['num_tries']
    app_template = page+'.html'

    if constants.NEXT_BACKEND_GLOBAL_HOST:
        host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                         constants.NEXT_BACKEND_GLOBAL_PORT)
    else:
        host_url = ''
        
    return render_template(app_template, host_url=host_url, exp_uid=exp_uid,
                           widget_key=widget_key, num_tries=num_tries), \
                           200, {'Cache-Control':'private, max-age=0, no-cache, no-store'}

