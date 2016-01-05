#!/usr/bin/python
"""
Helper methods for database backup and restore.
"""
import shutil
import subprocess
import next.constants as constants

def make_mongodump(name,exp_uid_list=[]):
    if len(exp_uid_list)==0:
        subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port} '
                         '--out dump/mongo_dump_{name}').format(hostname=constants.MONGODB_HOST,
                                                          port=constants.MONGODB_PORT,
                                                          name=name),
                        shell=True)
    else:
        exp_uid_list_str = '["'+'","'.join(exp_uid_list)+'"]'

        query_str = '\'{ $or: [ {"exp_uid":{$in:%s}}, {"object_id":{$in:%s}} ] }\'' %  (exp_uid_list_str,exp_uid_list_str)

        subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port} '
                         '--out dump/mongo_dump_{name} --query {query_str}').format(hostname=constants.MONGODB_HOST,
                                                          port=constants.MONGODB_PORT,
                                                          name=name,
                                                          query_str=query_str),
                        shell=True)
    subprocess.call(('tar czf dump/{name}.tar.gz '
                     'dump/mongo_dump_{name}').format(name=name),
                    shell=True)
    subprocess.call(('rm -r dump/mongo_dump_{name}').format(name=name),
                    shell=True)
    return 'dump/{}.tar.gz'.format(name)

# { $or: [ { quantity: { $lt: 20 } }, { price: 10 } ] }
 # db.raffle.find({"ticket_no" : {"$in" : [725, 542, 390]}})
 # mongodump --host $MONGODB_PORT_27017_TCP_ADDR:$MONGODB_PORT_27017_TCP_PORT --query '{ $or: [ {"exp_uid":{$in:["974e9c080caeaabff0591e64f3bc15"]}}, {"object_id":{$in:["974e9c080caeaabff0591e64f3bc15"]}} ] }'


    
def remove_mongodump(name):
    subprocess.call(('rm {path}/{name}').format(path='/dump',
                                                name=name),
                    shell=True)

def restore_mongodump(zip_file, name):
    # zip_file is a file object
    zip_file.save('dump/mongo_dump_restore.tar.gz')
    subprocess.call('tar -xvf dump/mongo_dump_restore.tar.gz',shell=True)
    subprocess.call(('/usr/bin/mongorestore --host {hostname} --port {port} '
                     'dump/mongo_dump').format(hostname=constants.MONGODB_HOST,
                                               port=constants.MONGODB_PORT),
                    shell=True)
    subprocess.call('rm dump/mongo_dump_restore.tar.gz',shell=True)
    subprocess.call('rm -rf dump/mongo_dump',shell=True)

# import next.database.database_lib as db_lib
# >>> db_lib.make_mongodump('test_619')