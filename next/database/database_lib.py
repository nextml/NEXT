#!/usr/bin/python
"""
Helper methods for database backup and restore.
"""
import shutil
import subprocess
import next.constants as constants

def make_mongodump(name):
    subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port} '
                     '--out dump/mongo_dump').format(hostname=constants.MONGODB_HOST,
                                                      port=constants.MONGODB_PORT),
                    shell=True)
    subprocess.call(('tar czf {path}/{name}.tar.gz '
                     'dump/mongo_dump').format(path='dump',
                                                name=name),
                    shell=True)
    
    return 'dump/{}.tar.gz'.format(name)
    
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

