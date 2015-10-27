#!/usr/bin/python
"""
Helper methods for database backup and restore.
"""

import subprocess
import next.constants as constants

def make_mongodump(name):
    print "in make_mongodump"
    subprocess.call(('/usr/bin/mongodump -vvvvv --host {hostname}:{port}'
                     '--out dump/mongo_dump').format(hostname=constants.MONGODB_HOST,
                                                      port=constants.MONGODB_PORT),
                    shell=True)
    subprocess.call(('tar czf {path}/{name}'
                     'dump/mongo_dump').format(path='/dump',
                                                name=name),
                    shell=True)
    
    return 'dump/{}.tar.gz'.format(name)
    
def remove_mongodump(name):
    subprocess.call(('rm {path}/{name}').format(path='/dump',
                                                name=name),
                    shell=True)
