import pkg_resources as pr
import os
from os.path import join
import json

resource_package = __name__
OBO_DIR = pr.resource_filename(resource_package, "obo")
PREFIX_TO_FNAME = pr.resource_filename(resource_package,
    "ont_prefix_to_filename.json")

def ontology_name_to_location():
    prefix_to_location = {}
    with open(PREFIX_TO_FNAME, "r") as f:
        for prefix, fname in json.load(f).items():
            prefix_to_location[prefix] = join(OBO_DIR, fname)
    return prefix_to_location
