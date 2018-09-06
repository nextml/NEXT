from StringIO import StringIO
import pandas as pd
from flask import Flask, send_file, request, abort
from flask_restful import Resource, reqparse
import traceback

import json
from io import BytesIO
import zipfile

import next.utils
import next.utils as utils
import next.api.api_util as api_util
from next.api.api_util import APIArgument
from next.api.resource_manager import ResourceManager
from next.database_client.DatabaseAPI import DatabaseAPI
from next.logging_client.LoggerAPI import LoggerAPI
from next.apps.App import App

db = DatabaseAPI()
ell = LoggerAPI()

resource_manager = ResourceManager()

# Request parser. Checks that necessary dictionary keys are available in a given resource.
# We rely on learningLib functions to ensure that all necessary arguments are available and parsed.
post_parser = reqparse.RequestParser(argument_class=APIArgument)

# Custom errors for GET and POST verbs on experiment resource
meta_error = {
    "ExpDoesNotExistError": {
        "message": "No experiment with the specified experiment ID exists.",
        "code": 400,
        "status": "FAIL",
    }
}

meta_success = {"code": 200, "status": "OK"}

# Participants resource class
class Targets(Resource):
    def get(self, exp_uid):
        app_id = resource_manager.get_app_id(exp_uid)
        app = App(app_id, exp_uid, db, ell)
        butler = app.butler
        return butler.targets.get_targetset(exp_uid)
