import os

from flask import Blueprint, render_template, flash, request, redirect, url_for

import next.constants as constants
from next.api.resource_manager import ResourceManager
import next.utils as utils

resource_manager = ResourceManager()
query_page = Blueprint('query_page',
                       __name__,
                       template_folder='templates',
                       static_folder='static')


@query_page.route('/query_page/<page>')
@query_page.route('/query_page/<page>/<exp_uid>')
def load_page(page, exp_uid=None):
    experiment = resource_manager.get_experiment(exp_uid)
    app_template = page + '.html'
    if constants.NEXT_BACKEND_GLOBAL_HOST:
        host_url = 'http://{}:{}'.format(constants.NEXT_BACKEND_GLOBAL_HOST,
                                         constants.NEXT_BACKEND_GLOBAL_PORT)
    else:
        host_url = ''

    part_id = request.args.get('participant', None)
    participant_uid = str(part_id) if part_id else part_id

    return render_template(app_template, host_url=host_url, exp_uid=exp_uid,
                           experiment=experiment,
                           participant_uid=participant_uid), \
        200, {'Cache-Control': 'private, max-age=0, no-cache, no-store'}
