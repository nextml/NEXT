import os
import yaml
import base64
import requests
from collections import OrderedDict


init_filename = 'init.yaml'
with open(init_filename, 'r') as f:
    init = yaml.load(f)

targets_filename = './strangefruit30.zip'
with open(targets_filename, 'r') as f:
    targets = f.read()


header = "data:application/{};base64,"
d = {'args': header.format('x-yaml') + base64.encodestring(yaml.dump(init)),
     'targets': header.format('zip') + base64.encodestring(targets),
     'key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
     'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
     'bucket_id': os.environ.get('AWS_BUCKET_NAME')}
d = OrderedDict(d)

host_url = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', 'localhost')
host_url = 'http://' + host_url + ':8000'

header = ['{}:{}'.format(key, len(item)) for key, item in d.items()]
header = ';'.join(header) + '\n'

to_send = ''.join([item for _, item in d.items()])

data = header + to_send

response = requests.post(host_url + '/assistant/init/experiment', data=data)

print(response)
print(response.json())
