from flask import Flask, request, send_file
from flask_restful import Resource, reqparse
import flask_restful.inputs

import next.utils
from next.api.resource_manager import ResourceManager

resource_manager = ResourceManager()
parser = reqparse.RequestParser()
parser.add_argument('retired', type=flask_restful.inputs.boolean)


class Retired(Resource):
    def get(self, exp_uid):
        return resource_manager.is_exp_retired(exp_uid)

    def post(self, exp_uid):
        args = parser.parse_args(strict=True)

        resource_manager.set_exp_retired(exp_uid, args['retired'])
