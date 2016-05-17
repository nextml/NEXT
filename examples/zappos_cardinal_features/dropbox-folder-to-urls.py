import os, sys
import dropbox
import requests
import json
from joblib import delayed, Parallel
import time
import pickle
import pandas as pd

# create a "Public folder" on Dropbox following the instructions at [1]
# (I need to test that the URL remains the same but it should)
#[1]:https://www.dropbox.com/en/help/16

dropbox_folder = 'Public/AllShoes2.2k'

assert 'DROPBOX_ACCESS_TOKEN' in os.environ, "We need this to access dropbox"
dropbox_key = os.getenv('DROPBOX_ACCESS_TOKEN')

dbx = dropbox.Dropbox(dropbox_key)

# dropbox API doesn't like when string ends in slash
if dropbox_folder[-1] == '/':
    dropbox_folder = dropbox_folder[:-1]
if dropbox_folder[0] != '/':
    dropbox_folder = '/' + dropbox_folder

urls = []
start = time.time()
for i, entry in enumerate(dbx.files_list_folder(dropbox_folder).entries):
    if '.DS' in entry.name:
        continue
    try:
        r = dbx.sharing_create_shared_link(entry.path_display)
    except:
        print("Error! I'm not sure what caused this; try rerunning?")
        print("Well, make sure that the folder you specified actually exists")
        print(entry, entry.name)
    urls += [r.url[:r.url.find('?')]]
    if i % 100 == 0:
        total_time = (time.time() - start) * 50e3 / 100
        print("estimated total hours = {}, assume 50k files".format(
                            total_time / (60*60)))
        start = time.time()

with open('urls2.2k-python.csv', 'w') as file_ :
    print("\n".join(urls), file=file_)
