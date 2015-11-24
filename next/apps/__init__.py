import os
full_path = os.path.realpath(__file__)
implemented_apps = next(os.walk(os.path.dirname(full_path)))[1]