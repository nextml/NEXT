#!/usr/bin/python
"""
Helper methods for database backup and restore.
"""
import shutil
import tempfile
import subprocess
import next.constants as constants
from pymongo import MongoClient

def make_mongodump(name,exp_uid_list=[]):
    tmp_dir = tempfile.mkdtemp()
    if len(exp_uid_list)==0:
        subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port} '
                         '--out {path}').format(hostname=constants.MONGODB_HOST,
                                                          port=constants.MONGODB_PORT,
                                                          path=tmp_dir),
                        shell=True)
    else:
        exp_uid_list_str = '["'+'","'.join(exp_uid_list)+'"]'

        query_str = '\'{ $or: [ {"exp_uid":{$in:%s}}, {"object_id":{$in:%s}} ] }\'' %  (exp_uid_list_str,exp_uid_list_str)

        # subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port} '
                         # '--out {path} --query {query_str}').format(hostname=constants.MONGODB_HOST,
        client = MongoClient(constants.MONGODB_HOST, constants.MONGODB_PORT)  
        for db in client.database_names():
          for col in client[db].collection_names():
            subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port} '
                         '--out {path} -d '+str(db)+' -c '+str(col)+' --query {query_str}').format(hostname=constants.MONGODB_HOST,                                            
                                                          port=constants.MONGODB_PORT,
                                                          path=tmp_dir,
                                                          query_str=query_str),
                        shell=True)
    subprocess.call('mkdir -p /dump',shell=True)
    subprocess.call(('tar czf /dump/{name} '
                     '-C {path} .').format(name=name,path=tmp_dir),
                    shell=True)
    
    shutil.rmtree(tmp_dir)
    return '/dump/{}'.format(name)

    
def remove_mongodump(name):
    subprocess.call(('rm /dump/{name}').format(name=name),
                    shell=True)

def restore_mongodump(src_filename):
    tmp_dir = tempfile.mkdtemp()
    subprocess.call(('tar -xvf {src_filename} -C {dst_path}').format(src_filename=src_filename,dst_path=tmp_dir),shell=True)
    subprocess.call(('/usr/bin/mongorestore --host {hostname} --port {port} '
                     '{path}').format(hostname=constants.MONGODB_HOST,
                                               port=constants.MONGODB_PORT,
                                               path=tmp_dir),
                    shell=True)
    shutil.rmtree(tmp_dir)


# import next.database.database_lib as db_lib
# >>> db_lib.make_mongodump('test_619')