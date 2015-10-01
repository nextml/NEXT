#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file was forked from the Apache Spark project and modified. Many
# thanks to those guys for a great time-saving file.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from __future__ import with_statement

import hashlib
import logging
import os
import pipes
import random
import shutil
import string
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time
import urllib2
import warnings
from datetime import datetime
from optparse import OptionParser
from sys import stderr, version_info

"""
# launch a new cluster of instance type "c3.8xlarge" (see http://www.ec2instances.info or below for other choices)
python next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem --instance-type=c3.8xlarge launch kevin_dev

# get the public-DNS of your machine
python next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem get-master kevin_dev

# rsync the next-discovery code up to your machine
python next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem rsync kevin_dev

# login to your machine manually or use
python next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem login kevin_dev

# restore from database file already on S3
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem --backup-filename=mongo_dump_next-test1.discovery.wisc.edu_2015-04-22_01:09:42.tar.gz restore kevin_dev

# display all files in a bucket with a given prefix. Useful if you need to find a database to backup from. Will display all files is prefix is not given
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem --bucket=next.discovery --prefix=mongo_dump_next-test1.discovery.wisc.edu  listbucket kevin_dev

# create a new S3 bucket and obtain the unique bucket name
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem createbucket kevin_dev

# force the current machine to perform a backup NOW to a designated filename
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem --backup-filename=this_is_a_custom_filename backup kevin_dev

# stop the current machine
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem stop kevin_dev

# start the current machine
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem start kevin_dev

# terminate the current machine
python  next_ec2.py --key-pair=next_key_1 --identity-file=/Users/kevinjamieson/aws_keys/next_key_1.pem destroy kevin_dev


"""

NEXT_BACKEND_GLOBAL_PORT = 8000
NEXT_FRONTEND_GLOBAL_PORT = 80
EC2_SRC_PATH = '/usr/local'
EC2_NEXT_PATH = EC2_SRC_PATH + '/next-discovery'
LOCAL_NEXT_PATH = './../'

DEFAULT_REGION = 'us-west-2'
DEFAULT_AMI = 'ami-6989a659'  # Ubuntu Server 14.04 LTS
DEFAULT_USER = 'ubuntu'
DEFAULT_INSTANCE_TYPE = 'm3.large'

import boto
from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType, EBSBlockDeviceType
from boto import ec2


class UsageError(Exception):
    pass


instance_info = {
"c1.medium" : { "cpu": 2, "memory": 1.7, "cost_per_hr": 0.13 },
"c1.xlarge" : { "cpu": 8, "memory": 7, "cost_per_hr": 0.52 },
"c3.large" : { "cpu": 2, "memory": 3.75, "cost_per_hr": 0.105 },
"c3.xlarge" : { "cpu": 4, "memory": 7.5, "cost_per_hr": 0.21 },
"c3.2xlarge" : { "cpu": 8, "memory": 15, "cost_per_hr": 0.42 },
"c3.4xlarge" : { "cpu": 16, "memory": 30, "cost_per_hr": 0.84 },
"c3.8xlarge" : { "cpu": 32, "memory": 60, "cost_per_hr": 1.68 },
"c4.large" : { "cpu": 2, "memory": 3.75, "cost_per_hr": 0.116 },
"c4.xlarge" : { "cpu": 4, "memory": 7.5, "cost_per_hr": 0.232 },
"c4.2xlarge" : { "cpu": 8, "memory": 15, "cost_per_hr": 0.464 },
"c4.4xlarge" : { "cpu": 16, "memory": 30, "cost_per_hr": 0.928 },
"c4.8xlarge" : { "cpu": 36, "memory": 60, "cost_per_hr": 1.856 },
"cc2.8xlarge" : { "cpu": 32, "memory": 60.5, "cost_per_hr": 2 },
"cr1.8xlarge" : { "cpu": 32, "memory": 244, "cost_per_hr": 3.5 },
"d2.xlarge" : { "cpu": 4, "memory": 30.5, "cost_per_hr": 0.69 },
"d2.2xlarge" : { "cpu": 8, "memory": 61, "cost_per_hr": 1.38 },
"d2.4xlarge" : { "cpu": 16, "memory": 122, "cost_per_hr": 2.76 },
"d2.8xlarge" : { "cpu": 36, "memory": 244, "cost_per_hr": 5.52 },
"g2.2xlarge" : { "cpu": 8, "memory": 15, "cost_per_hr": 0.65 },
"g2.8xlarge" : { "cpu": 32, "memory": 60, "cost_per_hr": 2.6 },
"hi1.4xlarge" : { "cpu": 16, "memory": 60.5, "cost_per_hr": 3.1 },
"hs1.8xlarge" : { "cpu": 16, "memory": 117, "cost_per_hr": 4.6 },
"i2.xlarge" : { "cpu": 4, "memory": 30.5, "cost_per_hr": 0.853 },
"i2.2xlarge" : { "cpu": 8, "memory": 61, "cost_per_hr": 1.705 },
"i2.4xlarge" : { "cpu": 16, "memory": 122, "cost_per_hr": 3.41 },
"i2.8xlarge" : { "cpu": 32, "memory": 244, "cost_per_hr": 6.82 },
"m1.small" : { "cpu": 1, "memory": 1.7, "cost_per_hr": 0.044 },
"m1.medium" : { "cpu": 1, "memory": 3.75, "cost_per_hr": 0.087 },
"m1.large" : { "cpu": 2, "memory": 7.5, "cost_per_hr": 0.175 },
"m1.xlarge" : { "cpu": 4, "memory": 15, "cost_per_hr": 0.35 },
"m2.xlarge" : { "cpu": 2, "memory": 17.1, "cost_per_hr": 0.245 },
"m2.2xlarge" : { "cpu": 4, "memory": 34.2, "cost_per_hr": 0.49 },
"m2.4xlarge" : { "cpu": 8, "memory": 68.4, "cost_per_hr": 0.98 },
"m3.medium" : { "cpu": 1, "memory": 3.75, "cost_per_hr": 0.07 },
"m3.large" : { "cpu": 2, "memory": 7.5, "cost_per_hr": 0.14 },
"m3.xlarge" : { "cpu": 4, "memory": 15, "cost_per_hr": 0.28 },
"m3.2xlarge" : { "cpu": 8, "memory": 30, "cost_per_hr": 0.56 },
"r3.large" : { "cpu": 2, "memory": 15, "cost_per_hr": 0.175 },
"r3.xlarge" : { "cpu": 4, "memory": 30.5, "cost_per_hr": 0.35 },
"r3.2xlarge" : { "cpu": 8, "memory": 61, "cost_per_hr": 0.7 },
"r3.4xlarge" : { "cpu": 16, "memory": 122, "cost_per_hr": 1.4 },
"r3.8xlarge" : { "cpu": 32, "memory": 244, "cost_per_hr": 2.8 },
"t1.micro" : { "cpu": 1, "memory": 0.615, "cost_per_hr": 0.02 },
"t2.micro" : { "cpu": 1, "memory": 1, "cost_per_hr": 0.013 },
"t2.small" : { "cpu": 1, "memory": 2, "cost_per_hr": 0.026 },
"t2.medium" : { "cpu": 2, "memory": 4, "cost_per_hr": 0.052 },
}

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Configure and parse our command-line arguments
def parse_args():
    parser = OptionParser(
        prog="spark-ec2",
        version="%prog {v}".format(v=''),
        usage="%prog [options] <action> <cluster_name>\n\n"
        + "<action> can be: launch, destroy, login, stop, start, get-master, reboot-slaves, rsync, backup, restore, docker_up, docker_login, listbucket, createbucket")
    parser.add_option(
        "-s", "--slaves", type="int", default=0,
        help="Number of slaves to launch (default: %default)")
    parser.add_option(
        "-k", "--key-pair",
        help="Key pair to use on instances")
    parser.add_option(
        "-i", "--identity-file",
        help="SSH private key file to use for logging into instances")
    parser.add_option(
        "-t", "--instance-type", default=DEFAULT_INSTANCE_TYPE,
        help="Type of instance to launch (default: %default). " +
             "WARNING: must be 64-bit; small instances won't work")
    parser.add_option(
        "-m", "--master-instance-type", default="",
        help="Master instance type (leave empty for same as instance-type)")
    parser.add_option(
        "-r", "--region", default=DEFAULT_REGION,
        help="EC2 region zone to launch instances in")
    parser.add_option(
        "-z", "--zone", default="",
        help="Availability zone to launch instances in, or 'all' to spread " +
             "slaves across multiple (an additional $0.01/Gb for bandwidth" +
             "between zones applies) (default: a single zone chosen at random)")
    parser.add_option("-a", "--ami", default=DEFAULT_AMI,
        help="Amazon Machine Image ID to use (default: %default). ")
    parser.add_option(
        "-D", metavar="[ADDRESS:]PORT", dest="proxy_port",
        help="Use SSH dynamic port forwarding to create a SOCKS proxy at " +
             "the given local address (for use with login)")
    parser.add_option(
        "--resume", action="store_true", default=False,
        help="Resume installation on a previously launched cluster " +
             "(for debugging)")
    parser.add_option(
        "--ebs-vol-size", metavar="SIZE", type="int", default=0,
        help="Size (in GB) of each EBS volume.")
    parser.add_option(
        "--ebs-vol-type", default="standard",
        help="EBS volume type (e.g. 'gp2', 'standard').")
    parser.add_option(
        "--ebs-vol-num", type="int", default=1,
        help="Number of EBS volumes to attach to each node as /vol[x]. " +
             "The volumes will be deleted when the instances terminate. " +
             "Only possible on EBS-backed AMIs. " +
             "EBS volumes are only attached if --ebs-vol-size > 0." +
             "Only support up to 8 EBS volumes.")
    parser.add_option(
        "--root-vol-size", metavar="SIZE", type="int", default=120,
        help="Size (in GB) of the root volume.")
    parser.add_option(
        "--root-vol-num", type="int", default=1,
        help="Number of root volumes to attach to each node")
    parser.add_option("--placement-group", type="string", default=None,
                      help="Which placement group to try and launch " +
                      "instances into. Assumes placement group is already " +
                      "created.")
    parser.add_option(
        "--swap", metavar="SWAP", type="int", default=1024,
        help="Swap space to set up per node, in MB (default: %default)")
    parser.add_option(
        "--spot-price", metavar="PRICE", type="float",
        help="If specified, launch slaves as spot instances with the given " +
             "maximum price (in dollars)")
    parser.add_option(
        "-u", "--user", default=DEFAULT_USER,
        help="The SSH user you want to connect as (default: %default)")
    parser.add_option(
        "--delete-groups", action="store_true", default=False,
        help="When destroying a cluster, delete the security groups that were created")
    parser.add_option(
        "--use-existing-master", action="store_true", default=False,
        help="Launch fresh slaves, but use an existing stopped master if possible")
    parser.add_option(
        "--worker-instances", type="int", default=1,
        help="Number of instances per worker: variable SPARK_WORKER_INSTANCES (default: %default)")
    parser.add_option(
        "--master-opts", type="string", default="",
        help="Extra options to give to master through SPARK_MASTER_OPTS variable " +
             "(e.g -Dspark.worker.timeout=180)")
    parser.add_option(
        "--user-data", type="string", default="",
        help="Path to a user-data file (most AMI's interpret this as an initialization script)")
    parser.add_option(
        "--authorized-address", type="string", default="0.0.0.0/0",
        help="Address to authorize on created security groups (default: %default)")
    parser.add_option(
        "--additional-security-group", type="string", default="",
        help="Additional security group to place the machines in")
    parser.add_option(
        "--copy-aws-credentials", action="store_true", default=False,
        help="Add AWS credentials to hadoop configuration to allow Spark to access S3")
    parser.add_option(
        "--subnet-id", default=None, help="VPC subnet to launch instances in")
    parser.add_option(
        "--vpc-id", default=None, help="VPC to launch instances in")
    parser.add_option(
        "--backup-filename", default=None, help="The filename (with extension) of the backup filename on EC2 to backup to or restore from. Only has effect on action={backup,restore}")
    parser.add_option(
        "--bucket", default=None, help="The name (with extension) of unique bucket to list files from. Only has effect on action={listbucket}")
    parser.add_option(
        "--prefix", default=None, help="A prefix to filter files in a bucket with. Only has effect on action={listbucket}")

    (opts, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)
    (action, cluster_name) = args

    # Boto config check
    # http://boto.cloudhackers.com/en/latest/boto_config_tut.html
    home_dir = os.getenv('HOME')
    if home_dir is None or not os.path.isfile(home_dir + '/.boto'):
        if not os.path.isfile('/etc/boto.cfg'):
            if os.getenv('AWS_ACCESS_KEY_ID') is None:
                print >> stderr, ("ERROR: The environment variable AWS_ACCESS_KEY_ID " +
                                  "must be set")
                sys.exit(1)
            if os.getenv('AWS_SECRET_ACCESS_KEY') is None:
                print >> stderr, ("ERROR: The environment variable AWS_SECRET_ACCESS_KEY " +
                                  "must be set")
                sys.exit(1)
    return (opts, action, cluster_name)


# Get the EC2 security group of the given name, creating it if it doesn't exist
def get_or_make_group(conn, name, vpc_id):
    groups = conn.get_all_security_groups()
    group = [g for g in groups if g.name == name]
    if len(group) > 0:
        return group[0]
    else:
        print "Creating security group " + name
        return conn.create_security_group(name, "NEXT EC2 group", vpc_id)


# Check whether a given EC2 instance object is in a state we consider active,
# i.e. not terminating or terminated. We count both stopping and stopped as
# active since we can restart stopped clusters.
def is_active(instance):
    return (instance.state in ['pending', 'running', 'stopping', 'stopped'])


# Launch a cluster of the given name, by setting up its security groups,
# and then starting new instances in them.
# Returns a tuple of EC2 reservation objects for the master and slaves
# Fails if there already instances running in the cluster's groups.
def launch_cluster(conn, opts, cluster_name):
    if opts.identity_file is None:
        print >> stderr, "ERROR: Must provide an identity file (-i) for ssh connections."
        sys.exit(1)
    if opts.key_pair is None:
        print >> stderr, "ERROR: Must provide a key pair name (-k) to use on instances."
        sys.exit(1)

    user_data_content = None
    if opts.user_data:
        with open(opts.user_data) as user_data_file:
            user_data_content = user_data_file.read()

    print "Setting up security groups..."
    master_group = get_or_make_group(conn, cluster_name + "-master", opts.vpc_id)
    if opts.slaves>0: slave_group = get_or_make_group(conn, cluster_name + "-slaves", opts.vpc_id)
    authorized_address = opts.authorized_address
    if master_group.rules == []:  # Group was just now created
        if opts.slaves>0:
            if opts.vpc_id is None:
                master_group.authorize(src_group=master_group)
                master_group.authorize(src_group=slave_group)
            else:
                master_group.authorize(ip_protocol='icmp', from_port=-1, to_port=-1,
                                       src_group=master_group)
                master_group.authorize(ip_protocol='tcp', from_port=0, to_port=65535,
                                       src_group=master_group)
                master_group.authorize(ip_protocol='udp', from_port=0, to_port=65535,
                                       src_group=master_group)
                master_group.authorize(ip_protocol='icmp', from_port=-1, to_port=-1,
                                       src_group=slave_group)
                master_group.authorize(ip_protocol='tcp', from_port=0, to_port=65535,
                                       src_group=slave_group)
                master_group.authorize(ip_protocol='udp', from_port=0, to_port=65535,
                                       src_group=slave_group)
        master_group.authorize('tcp', 22, 22, authorized_address)
        master_group.authorize('tcp', NEXT_BACKEND_GLOBAL_PORT, NEXT_BACKEND_GLOBAL_PORT, authorized_address)
        #master_group.authorize('tcp', NEXT_FRONTEND_BASE_GLOBAL_PORT, NEXT_FRONTEND_BASE_GLOBAL_PORT, authorized_address)
        master_group.authorize('tcp', NEXT_FRONTEND_GLOBAL_PORT, NEXT_FRONTEND_GLOBAL_PORT, authorized_address)
        master_group.authorize('tcp', 5555, 5555, authorized_address)
        master_group.authorize('tcp', 8888, 8888, authorized_address)
        master_group.authorize('tcp', 15672, 15672, authorized_address)
        master_group.authorize('tcp', 28017, 28017, authorized_address)
    if opts.slaves>0 and slave_group.rules == []:  # Group was just now created
        if opts.vpc_id is None:
            slave_group.authorize(src_group=master_group)
            slave_group.authorize(src_group=slave_group)
        else:
            slave_group.authorize(ip_protocol='icmp', from_port=-1, to_port=-1,
                                  src_group=master_group)
            slave_group.authorize(ip_protocol='tcp', from_port=0, to_port=65535,
                                  src_group=master_group)
            slave_group.authorize(ip_protocol='udp', from_port=0, to_port=65535,
                                  src_group=master_group)
            slave_group.authorize(ip_protocol='icmp', from_port=-1, to_port=-1,
                                  src_group=slave_group)
            slave_group.authorize(ip_protocol='tcp', from_port=0, to_port=65535,
                                  src_group=slave_group)
            slave_group.authorize(ip_protocol='udp', from_port=0, to_port=65535,
                                  src_group=slave_group)
        slave_group.authorize('tcp', 22, 22, authorized_address)

    # Check if instances are already running in our groups
    existing_masters, existing_slaves = get_existing_cluster(conn, opts, cluster_name,
                                                             die_on_error=False)
    if existing_slaves or (existing_masters and not opts.use_existing_master):
        print >> stderr, ("ERROR: There are already instances running in " +
                          "the desired group")
        sys.exit(1)

    # we use group ids to work around https://github.com/boto/boto/issues/350
    additional_group_ids = []
    if opts.additional_security_group:
        additional_group_ids = [sg.id
                                for sg in conn.get_all_security_groups()
                                if opts.additional_security_group in (sg.name, sg.id)]
    print "Launching instances..."

    try:
        image = conn.get_all_images(image_ids=[opts.ami])[0]
    except:
        print >> stderr, "Could not find AMI " + opts.ami
        print colors.FAIL + '[error] The startup script could not find your AMI. '\
                + 'You are either in the incorrect region (in which case see [1]) '\
                + 'or need to specify both the --region and --ami flags.\n'\
                + 'example: --region={0} --ami={1}\n'.format(DEFAULT_REGION, DEFAULT_AMI)\
                + '\n'\
                + '[1]:https://github.com/nextml/NEXT/issues/11'\
                + colors.ENDC
        sys.exit(1)

    # Create block device mapping so that we can add EBS volumes if asked to.
    # The first drive is attached as /dev/sds, 2nd as /dev/sdt, ... /dev/sdz
    block_map = BlockDeviceMapping()
    # if opts.instance_type.startswith('m3.'):
    for i in range(opts.root_vol_num):
        dev = EBSBlockDeviceType()
        dev.size = opts.root_vol_size
        # dev.ephemeral_name = 'ephemeral%d' % i
        # The first ephemeral drive is /dev/sda1.
        name = '/dev/sd' + string.letters[i] + str(i+1)
        block_map[name] = dev

    if opts.ebs_vol_size > 0:
        for i in range(opts.ebs_vol_num):
            device = EBSBlockDeviceType()
            device.size = opts.ebs_vol_size
            device.volume_type = opts.ebs_vol_type
            device.delete_on_termination = True
            block_map["/dev/sd" + chr(ord('s') + i)] = device

    # Launch slaves
    if opts.slaves>0:
        if opts.spot_price is not None:
            # Launch spot instances with the requested price
            print ("Requesting %d slaves as spot instances with price $%.3f" %
                   (opts.slaves, opts.spot_price))
            zones = get_zones(conn, opts)
            num_zones = len(zones)
            i = 0
            my_req_ids = []
            for zone in zones:
                num_slaves_this_zone = get_partition(opts.slaves, num_zones, i)
                slave_reqs = conn.request_spot_instances(
                    price=opts.spot_price,
                    image_id=opts.ami,
                    launch_group="launch-group-%s" % cluster_name,
                    placement=zone,
                    count=num_slaves_this_zone,
                    key_name=opts.key_pair,
                    security_group_ids=[slave_group.id] + additional_group_ids,
                    instance_type=opts.instance_type,
                    block_device_map=block_map,
                    subnet_id=opts.subnet_id,
                    placement_group=opts.placement_group,
                    user_data=user_data_content)
                my_req_ids += [req.id for req in slave_reqs]
                i += 1

            print "Waiting for spot instances to be granted..."
            try:
                while True:
                    time.sleep(10)
                    reqs = conn.get_all_spot_instance_requests()
                    id_to_req = {}
                    for r in reqs:
                        id_to_req[r.id] = r
                    active_instance_ids = []
                    for i in my_req_ids:
                        if i in id_to_req and id_to_req[i].state == "active":
                            active_instance_ids.append(id_to_req[i].instance_id)
                    if len(active_instance_ids) == opts.slaves:
                        print "All %d slaves granted" % opts.slaves
                        reservations = conn.get_all_reservations(active_instance_ids)
                        slave_nodes = []
                        for r in reservations:
                            slave_nodes += r.instances
                        break
                    else:
                        print "%d of %d slaves granted, waiting longer" % (
                            len(active_instance_ids), opts.slaves)
            except:
                print "Canceling spot instance requests"
                conn.cancel_spot_instance_requests(my_req_ids)
                # Log a warning if any of these requests actually launched instances:
                (master_nodes, slave_nodes) = get_existing_cluster(
                    conn, opts, cluster_name, die_on_error=False)
                running = len(master_nodes) + len(slave_nodes)
                if running:
                    print >> stderr, ("WARNING: %d instances are still running" % running)
                sys.exit(0)
        else:
            # Launch non-spot instances
            zones = get_zones(conn, opts)
            num_zones = len(zones)
            i = 0
            slave_nodes = []
            for zone in zones:
                num_slaves_this_zone = get_partition(opts.slaves, num_zones, i)
                if num_slaves_this_zone > 0:
                    slave_res = image.run(key_name=opts.key_pair,
                                          security_group_ids=[slave_group.id] + additional_group_ids,
                                          instance_type=opts.instance_type,
                                          placement=zone,
                                          min_count=num_slaves_this_zone,
                                          max_count=num_slaves_this_zone,
                                          block_device_map=block_map,
                                          subnet_id=opts.subnet_id,
                                          placement_group=opts.placement_group,
                                          user_data=user_data_content)
                    slave_nodes += slave_res.instances
                    print "Launched %d slaves in %s, regid = %s" % (num_slaves_this_zone,
                                                                    zone, slave_res.id)
                i += 1
    else:
        slave_nodes = []

    # Launch or resume masters
    if existing_masters:
        print "Starting master..."
        for inst in existing_masters:
            if inst.state not in ["shutting-down", "terminated"]:
                inst.start()
        master_nodes = existing_masters
    else:
        master_type = opts.master_instance_type
        if master_type == "":
            master_type = opts.instance_type
        if opts.zone == 'all':
            opts.zone = random.choice(conn.get_all_zones()).name
        master_res = image.run(key_name=opts.key_pair,
                               security_group_ids=[master_group.id] + additional_group_ids,
                               instance_type=master_type,
                               placement=opts.zone,
                               min_count=1,
                               max_count=1,
                               block_device_map=block_map,
                               subnet_id=opts.subnet_id,
                               placement_group=opts.placement_group,
                               user_data=user_data_content)

        master_nodes = master_res.instances
        print "Launched master in %s, regid = %s" % (opts.zone, master_res.id)

    # This wait time corresponds to SPARK-4983
    print "Waiting for AWS to propagate instance metadata..."
    time.sleep(5)
    # Give the instances descriptive names
    for master in master_nodes:
        master.add_tag(
            key='Name',
            value='{cn}-master-{iid}'.format(cn=cluster_name, iid=master.id))
    for slave in slave_nodes:
        slave.add_tag(
            key='Name',
            value='{cn}-slave-{iid}'.format(cn=cluster_name, iid=slave.id))

    # Return all the instances
    return (master_nodes, slave_nodes)


# Get the EC2 instances in an existing cluster if available.
# Returns a tuple of lists of EC2 instance objects for the masters and slaves


def get_existing_cluster(conn, opts, cluster_name, die_on_error=True):
    print "Searching for existing cluster " + cluster_name + "..."
    reservations = conn.get_all_reservations()
    master_nodes = []
    slave_nodes = []
    for res in reservations:
        active = [i for i in res.instances if is_active(i)]
        for inst in active:
            group_names = [g.name for g in inst.groups]
            if (cluster_name + "-master") in group_names:
                master_nodes.append(inst)
            elif (cluster_name + "-slaves") in group_names:
                slave_nodes.append(inst)
    if any((master_nodes, slave_nodes)):
        print "Found %d master(s), %d slaves" % (len(master_nodes), len(slave_nodes))
    if master_nodes != [] or not die_on_error:
        return (master_nodes, slave_nodes)
    else:
        if master_nodes == [] and slave_nodes != []:
            print >> sys.stderr, "ERROR: Could not find master in group " + cluster_name + "-master"
        else:
            print >> sys.stderr, "ERROR: Could not find any existing cluster"
        sys.exit(1)


# Deploy configuration files and run setup scripts on a newly launched
# or started EC2 cluster.
def setup_cluster(conn, master_nodes, slave_nodes, opts, deploy_ssh_key):
    master = master_nodes[0].public_dns_name
    if deploy_ssh_key:
        print "Generating cluster's SSH key on master..."
        key_setup = """
          [ -f ~/.ssh/id_rsa ] ||
            (ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa &&
             cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys)
        """
        ssh(master, opts, key_setup)
        dot_ssh_tar = ssh_read(master, opts, ['tar', 'c', '.ssh'])
        print "Transferring cluster's SSH key to slaves..."
        for slave in slave_nodes:
            print slave.public_dns_name
            ssh_write(slave.public_dns_name, opts, ['tar', 'x'], dot_ssh_tar)

    print "Running setup on master..."
    setup_next_cluster(master, opts)
    print "Done!"

    print "Start rsync of local next-discovery source code up"
    rsync_dir(LOCAL_NEXT_PATH, EC2_NEXT_PATH, opts, master)
    print "Done!"

    print "Running docker-compose up on master..."
    docker_up(opts, master_nodes, slave_nodes)


def rsync_dir(local_src_dir, ec2_dest_dir, opts, host):
    command = [
        'rsync', '--exclude=.git', '--exclude=archive', '-rve',
        stringify_command(ssh_command(opts)),
        "%s" % local_src_dir,
        "%s@%s:%s/" % (opts.user, host, ec2_dest_dir)
    ]
    subprocess.check_call(command)

def setup_next_cluster(master, opts):
    # Create a temp directory in which we will place all the files to be
    # deployed after we substitue template parameters in them
    tmp_dir = tempfile.mkdtemp()
    with open('./templates/setup.sh') as src:
        with open(tmp_dir+'/setup.sh', "w") as dest:
            text = src.read()
            # text = text.replace("{{ environment_variables }}",env_vars)
            dest.write(text)
            dest.close()

    # rsync the whole directory over to the master machine
    ssh(master, opts, "sudo rm -rf " + EC2_NEXT_PATH)
    ssh(master, opts, "sudo mkdir " + EC2_NEXT_PATH)
    ssh(master, opts, "sudo chmod 777 " + EC2_NEXT_PATH)
    command = [
        'rsync', '-rv',
        '-e', stringify_command(ssh_command(opts)),
        "%s/" % tmp_dir,
        "%s@%s:%s/" % (opts.user, master, EC2_NEXT_PATH)
    ]
    subprocess.check_call(command)
    # Remove the temp directory we created above
    shutil.rmtree(tmp_dir)

    ssh(master, opts, "sudo chmod 777 " + EC2_NEXT_PATH + '/' + 'setup.sh')
    ssh(master, opts, 'sudo ' + EC2_NEXT_PATH + '/' + 'setup.sh')


def docker_up(opts, master_nodes, slave_nodes):
    rsync_docker_config(opts, master_nodes, slave_nodes)
    master = master_nodes[0].public_dns_name

    ssh(master, opts, "sudo chmod 777 " + EC2_NEXT_PATH + '/' + 'docker_up.sh')
    ssh(master, opts, 'sudo ' + EC2_NEXT_PATH + '/' + 'docker_up.sh')


def docker_login(opts, master_nodes, slave_nodes):
    rsync_docker_config(opts, master_nodes, slave_nodes)
    master = master_nodes[0].public_dns_name

    import signal
    def preexec_function():
        # Ignore the SIGINT signal by setting the handler to the standard
        # signal handler SIG_IGN.
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    ssh(master, opts, "sudo chmod 777 " + EC2_NEXT_PATH + '/' + 'docker_login.sh')
    ssh(master, opts, 'sudo ' + EC2_NEXT_PATH + '/' + 'docker_login.sh')


def list_bucket(opts):
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    conn = boto.connect_s3( AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY )
    print "Trying to connect to bucket %s"%(opts.bucket)
    try:
        bucket = conn.get_bucket( opts.bucket )
        if hasattr(opts,'prefix'):
            print [ key.name.encode( "utf-8" ) for key in bucket.list(prefix=opts.prefix) ]
        else:
            print [ key.name.encode( "utf-8" ) for key in bucket.list() ]

    except boto.exception.S3ResponseError, e:
        print "This bucket does not exist. Please create a new bucket using createbucket command."

def createbucket(opts):
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    conn = boto.connect_s3( AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY )

    gotbucket = False
    while not gotbucket:
        bucket_uid = '%030x' % random.randrange(16**30)
        try:
            newbucket = conn.create_bucket(bucket_uid)
            gotbucket = True
        except boto.exception.S3CreateError, e:
            pass

    print 'Your AWS S3 bucket has been successfully created with bucket name set as: ', bucket_uid
    print
    print 'To automatically use this bucket, input the following command into your terminal:'
    print 'export AWS_BUCKET_NAME='+bucket_uid

def rsync_docker_config(opts, master_nodes, slave_nodes):
    master = master_nodes[0].public_dns_name

    opts.master_instance_type = master_nodes[0].instance_type
    if len(slave_nodes)>0:
        opts.instance_type = slave_nodes[0].instance_type

    master_num_cpus = instance_info[opts.master_instance_type]['cpu']
    slave_num_cpus = instance_info[opts.instance_type]['cpu']

    # Create a temp directory in which we will place all the files to be
    # deployed after we substitue template parameters in them
    tmp_dir = tempfile.mkdtemp()

    master_environment_vars = {
        "MASTER_LIST": ','.join([i.public_dns_name for i in master_nodes]),
        "ACTIVE_MASTER": master,
        "SLAVE_LIST": ','.join([i.public_dns_name for i in slave_nodes]),
        "NEXT_BACKEND_GLOBAL_HOST": master,
        "NEXT_BACKEND_GLOBAL_PORT": NEXT_BACKEND_GLOBAL_PORT,
        "NEXT_FRONTEND_GLOBAL_HOST":master,
        "NEXT_FRONTEND_GLOBAL_PORT":NEXT_FRONTEND_GLOBAL_PORT,
        "AWS_ACCESS_ID":os.getenv('AWS_ACCESS_KEY_ID'),
        "AWS_SECRET_ACCESS_KEY":os.getenv('AWS_SECRET_ACCESS_KEY'),
        "AWS_BUCKET_NAME":os.getenv('AWS_BUCKET_NAME','next-database-backups')
    }
    with open('./templates/docker_login.sh') as src:
        with open(tmp_dir+'/docker_login.sh', "w") as dest:
            text = src.read()
            env_vars = ''
            for key in master_environment_vars:
                env_vars += 'export ' + str(key) + '=' + str(master_environment_vars[key]) + '\n'
            text = text.replace("{{ environment_variables }}",env_vars)
            dest.write(text)
            dest.close()

    with open('./templates/docker_up.sh') as src:
        with open(tmp_dir+'/docker_up.sh', "w") as dest:
            text = src.read()
            env_vars = ''
            for key in master_environment_vars:
                env_vars += 'export ' + str(key) + '=' + str(master_environment_vars[key]) + '\n'
            text = text.replace("{{ environment_variables }}",env_vars)
            dest.write(text)
            dest.close()


    num_sync_workers = 6  # should be abotu the number of active algorithms
    unicorn_multiplier = .15
    docker_compose_template_vars = {
        "DATABASE_NUM_GUNICORN_WORKERS":int(unicorn_multiplier*master_num_cpus+1),
        "CELERY_SYNC_WORKER_COUNT": num_sync_workers,
        "CELERY_ASYNC_WORKER_COUNT":2,
        "CELERY_THREADS_PER_ASYNC_WORKER":max(1,int(.35*master_num_cpus)),
        "NEXT_BACKEND_NUM_GUNICORN_WORKERS":int(unicorn_multiplier*master_num_cpus+1),
        "NEXT_BACKEND_GLOBAL_PORT":NEXT_BACKEND_GLOBAL_PORT,
        "NEXT_FRONTEND_NUM_GUNICORN_WORKERS":int(unicorn_multiplier*master_num_cpus+1),
        "NEXT_FRONTEND_GLOBAL_PORT":NEXT_FRONTEND_GLOBAL_PORT
    }
    with open('./templates/docker-compose.yml') as src:
        with open(tmp_dir+'/docker-compose.yml', "w") as dest:
            text = src.read()
            env_vars = ''
            for key in docker_compose_template_vars:
                text = text.replace("{{" + key + "}}",str(docker_compose_template_vars[key]))
            dest.write(text)
            dest.close()
            print text


    # rsync the whole directory over to the master machine
    command = [
        'rsync', '-rv',
        '-e', stringify_command(ssh_command(opts)),
        "%s/" % tmp_dir,
        "%s@%s:%s/" % (opts.user, master, EC2_NEXT_PATH)
    ]
    subprocess.check_call(command)
    # Remove the temp directory we created above
    shutil.rmtree(tmp_dir)


def is_ssh_available(host, opts, print_ssh_output=True):
    """
    Check if SSH is available on a host.
    """
    s = subprocess.Popen(
        ssh_command(opts) + ['-t', '-t', '-o', 'ConnectTimeout=3',
                             '%s@%s' % (opts.user, host), stringify_command('true')],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT  # we pipe stderr through stdout to preserve output order
    )
    cmd_output = s.communicate()[0]  # [1] is stderr, which we redirected to stdout

    if s.returncode != 0 and print_ssh_output:
        # extra leading newline is for spacing in wait_for_cluster_state()
        print textwrap.dedent("""\n
            Warning: SSH connection error. (This could be temporary.)
            Host: {h}
            SSH return code: {r}
            SSH output: {o}
        """).format(
            h=host,
            r=s.returncode,
            o=cmd_output.strip()
        )

    return s.returncode == 0


def is_cluster_ssh_available(cluster_instances, opts):
    """
    Check if SSH is available on all the instances in a cluster.
    """
    for i in cluster_instances:
        if not is_ssh_available(host=i.public_dns_name, opts=opts):
            return False
    else:
        return True


def wait_for_cluster_state(conn, opts, cluster_instances, cluster_state):
    """
    Wait for all the instances in the cluster to reach a designated state.

    cluster_instances: a list of boto.ec2.instance.Instance
    cluster_state: a string representing the desired state of all the instances in the cluster
           value can be 'ssh-ready' or a valid value from boto.ec2.instance.InstanceState such as
           'running', 'terminated', etc.
           (would be nice to replace this with a proper enum: http://stackoverflow.com/a/1695250)
    """
    sys.stdout.write(
        "Waiting for cluster to enter '{s}' state.".format(s=cluster_state)
    )
    sys.stdout.flush()

    start_time = datetime.now()
    num_attempts = 0

    while True:
        time.sleep(10*( 1.*(num_attempts>0) + 0.1))  # seconds

        for i in cluster_instances:
            i.update()

        statuses = conn.get_all_instance_status(instance_ids=[i.id for i in cluster_instances])

        if cluster_state == 'ssh-ready':
            if all(i.state == 'running' for i in cluster_instances) and \
               all(s.system_status.status == 'ok' for s in statuses) and \
               all(s.instance_status.status == 'ok' for s in statuses) and \
               is_cluster_ssh_available(cluster_instances, opts):
                break
        else:
            if all(i.state == cluster_state for i in cluster_instances):
                break

        num_attempts += 1

        sys.stdout.write(".")
        sys.stdout.flush()

    sys.stdout.write("\n")

    end_time = datetime.now()
    print "Cluster is now in '{s}' state. Waited {t} seconds.".format(
        s=cluster_state,
        t=(end_time - start_time).seconds
    )


def stringify_command(parts):
    if isinstance(parts, str):
        return parts
    else:
        return ' '.join(map(pipes.quote, parts))


def ssh_args(opts):
    parts = ['-o', 'StrictHostKeyChecking=no']
    parts += ['-o', 'UserKnownHostsFile=/dev/null']
    if opts.identity_file is not None:
        parts += ['-i', opts.identity_file]
    return parts


def ssh_command(opts):
    return ['ssh'] + ssh_args(opts)


# Run a command on a host through ssh, retrying up to five times
# and then throwing an exception if ssh continues to fail.
def ssh(host, opts, command):
    tries = 0
    while True:
        try:
            return subprocess.check_call(
                ssh_command(opts) + ['-t', '-t', '%s@%s' % (opts.user, host),
                                     stringify_command(command)])
        except subprocess.CalledProcessError as e:
            if tries > 5:
                # If this was an ssh failure, provide the user with hints.
                if e.returncode == 255:
                    raise UsageError(
                        "Failed to SSH to remote host {0}.\n" +
                        "Please check that you have provided the correct --identity-file and " +
                        "--key-pair parameters and try again.".format(host))
                else:
                    raise e
            print >> stderr, \
                "Error executing remote command, retrying after 30 seconds: {0}".format(e)
            time.sleep(30)
            tries = tries + 1


# Backported from Python 2.7 for compatiblity with 2.6 (See SPARK-1990)
def _check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


def ssh_read(host, opts, command):
    return _check_output(
        ssh_command(opts) + ['%s@%s' % (opts.user, host), stringify_command(command)])


def ssh_write(host, opts, command, arguments):
    tries = 0
    while True:
        proc = subprocess.Popen(
            ssh_command(opts) + ['%s@%s' % (opts.user, host), stringify_command(command)],
            stdin=subprocess.PIPE)
        proc.stdin.write(arguments)
        proc.stdin.close()
        status = proc.wait()
        if status == 0:
            break
        elif tries > 5:
            raise RuntimeError("ssh_write failed with error %s" % proc.returncode)
        else:
            print >> stderr, \
                "Error {0} while executing remote command, retrying after 30 seconds".format(status)
            time.sleep(30)
            tries = tries + 1


# Gets a list of zones to launch instances in
def get_zones(conn, opts):
    if opts.zone == 'all':
        zones = [z.name for z in conn.get_all_zones()]
    else:
        zones = [opts.zone]
    return zones


# Gets the number of items in a partition
def get_partition(total, num_partitions, current_partitions):
    num_slaves_this_zone = total / num_partitions
    if (total % num_partitions) - current_partitions > 0:
        num_slaves_this_zone += 1
    return num_slaves_this_zone


def real_main():
    (opts, action, cluster_name) = parse_args()

    print 'opts : ' + str(opts)
    print
    print 'cluster_name : ' + str(cluster_name)
    print

    if opts.ebs_vol_num > 8:
        print >> stderr, "ebs-vol-num cannot be greater than 8"
        sys.exit(1)

    try:
        conn = ec2.connect_to_region(opts.region)
    except Exception as e:
        print >> stderr, (e)
        sys.exit(1)

    # Select an AZ at random if it was not specified.
    if opts.zone == "":
        opts.zone = random.choice(conn.get_all_zones()).name

    if action == "launch":
        print colors.OKBLUE + '[fyi]: NEXT has launched once red and blue messages start'\
                            + ' printing.\n' + colors.ENDC
        try:
            if opts.resume:
                (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
            else:
                (master_nodes, slave_nodes) = launch_cluster(conn, opts, cluster_name)

            print_dns_urls(prefix=True)
            wait_for_cluster_state(
                conn=conn,
                opts=opts,
                cluster_instances=(master_nodes + slave_nodes),
                cluster_state='ssh-ready'
            )
            print_dns_urls(instances=master_nodes + slave_nodes)
            setup_cluster(conn, master_nodes, slave_nodes, opts, True)
        except boto.exception.EC2ResponseError:
            print colors.FAIL + '[error] Your cluster failed to launch. This could happen'\
                  + ' for several reasons:\n'\
                  + '1. Are you in the right region? AMIs and keypairs are region\n'\
                  + '   specific. For more details, see [0] and [1].\n'\
                  + '2. Have you followed the setup guide at [2]?\n'\
                  + '\n[0]:https://github.com/nextml/NEXT/issues/11\n'\
                  + '[1]:https://github.com/nextml/NEXT/wiki/Troubleshooting\n'\
                  + '[2]:https://github.com/nextml/NEXT/wiki/NEXT-EC2-Launch-Tutorial'\
                 + colors.ENDC\

    elif action == "destroy":
        print "Are you sure you want to destroy the cluster %s?" % cluster_name
        print "The following instances will be terminated:"
        (master_nodes, slave_nodes) = get_existing_cluster(
            conn, opts, cluster_name, die_on_error=False)
        for inst in master_nodes + slave_nodes:
            print "> %s" % inst.public_dns_name

        msg = "ALL DATA ON ALL NODES WILL BE LOST!!\nDestroy cluster %s (y/N): " % cluster_name
        response = raw_input(msg)
        if response == "y":
            print "Terminating master..."
            for inst in master_nodes:
                inst.terminate()
            print "Terminating slaves..."
            for inst in slave_nodes:
                inst.terminate()

            # Delete security groups as well
            if opts.delete_groups:
                print "Deleting security groups (this will take some time)..."
                group_names = [cluster_name + "-master", cluster_name + "-slaves"]
                wait_for_cluster_state(
                    conn=conn,
                    opts=opts,
                    cluster_instances=(master_nodes + slave_nodes),
                    cluster_state='terminated'
                )
                attempt = 1
                while attempt <= 3:
                    print "Attempt %d" % attempt
                    groups = [g for g in conn.get_all_security_groups() if g.name in group_names]
                    success = True
                    # Delete individual rules in all groups before deleting groups to
                    # remove dependencies between them
                    for group in groups:
                        print "Deleting rules in security group " + group.name
                        for rule in group.rules:
                            for grant in rule.grants:
                                success &= group.revoke(ip_protocol=rule.ip_protocol,
                                                        from_port=rule.from_port,
                                                        to_port=rule.to_port,
                                                        src_group=grant)

                    # Sleep for AWS eventual-consistency to catch up, and for instances
                    # to terminate
                    time.sleep(30)  # Yes, it does have to be this long :-(
                    for group in groups:
                        try:
                            # It is needed to use group_id to make it work with VPC
                            conn.delete_security_group(group_id=group.id)
                            print "Deleted security group %s" % group.name
                        except boto.exception.EC2ResponseError:
                            success = False
                            print "Failed to delete security group %s" % group.name

                    # Unfortunately, group.revoke() returns True even if a rule was not
                    # deleted, so this needs to be rerun if something fails
                    if success:
                        break

                    attempt += 1

                if not success:
                    print "Failed to delete all security groups after 3 tries."
                    print "Try re-running in a few minutes."

    elif action == "login":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        master = master_nodes[0].public_dns_name
        print "Logging into master " + master + "..."
        proxy_opt = []
        if opts.proxy_port is not None:
            proxy_opt = ['-D', opts.proxy_port]
        subprocess.check_call(
            ssh_command(opts) + proxy_opt + ['-t', '-t', "%s@%s" % (opts.user, master)])

    elif action == "reboot-slaves":
        response = raw_input(
            "Are you sure you want to reboot the cluster " +
            cluster_name + " slaves?\n" +
            "Reboot cluster slaves " + cluster_name + " (y/N): ")
        if response == "y":
            (master_nodes, slave_nodes) = get_existing_cluster(
                conn, opts, cluster_name, die_on_error=False)
            print "Rebooting slaves..."
            for inst in slave_nodes:
                if inst.state not in ["shutting-down", "terminated"]:
                    print "Rebooting " + inst.id
                    inst.reboot()

    elif action == "get-master":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        print 'public_dns_name  : \t' + master_nodes[0].public_dns_name
        print 'instance_type \t : \t' + master_nodes[0].instance_type
        print 'num_cpus \t : \t' + str(instance_info[master_nodes[0].instance_type]['cpu'])
        print 'memory (GB) \t : \t' + str(instance_info[master_nodes[0].instance_type]['memory'])
        print 'cost ($/hr) \t : \t' + str(instance_info[master_nodes[0].instance_type]['cost_per_hr'])

    elif action == "rsync":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        master = master_nodes[0].public_dns_name
        rsync_dir(LOCAL_NEXT_PATH, EC2_NEXT_PATH, opts, master)
        rsync_docker_config(opts, master_nodes, slave_nodes)

    elif action == "docker_up":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        docker_up(opts, master_nodes, slave_nodes)

    elif action == "docker_login":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        docker_login(opts, master_nodes, slave_nodes)

    elif action == "backup":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        master = master_nodes[0].public_dns_name
        # opts.backup_filename
        command = "cd %s; sudo docker exec nextdiscovery_mongodbbackup_1 /bin/bash -c 'python ./next/database/database_backup.py %s' " % (EC2_NEXT_PATH,opts.backup_filename)
        ssh(master, opts, command)

    elif action == "restore":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        master = master_nodes[0].public_dns_name
        # opts.backup_filename
        command = "cd %s; sudo docker exec nextdiscovery_mongodbbackup_1 /bin/bash -c 'python ./next/database/database_restore.py %s' " % (EC2_NEXT_PATH,opts.backup_filename)
        ssh(master, opts, command)


    elif action == "listbucket":
        print "listbucket"
        list_bucket(opts)

    elif action == "createbucket":
        print "createbucket"
        createbucket(opts)

    elif action == "stop":
        response = raw_input(
            "Are you sure you want to stop the cluster " +
            cluster_name + "?\nDATA ON EPHEMERAL DISKS WILL BE LOST, " +
            "BUT THE CLUSTER WILL KEEP USING SPACE ON\n" +
            "AMAZON EBS IF IT IS EBS-BACKED!!\n" +
            "All data on spot-instance slaves will be lost.\n" +
            "Stop cluster " + cluster_name + " (y/N): ")
        if response == "y":
            (master_nodes, slave_nodes) = get_existing_cluster(
                conn, opts, cluster_name, die_on_error=False)
            print "Stopping master..."
            for inst in master_nodes:
                if inst.state not in ["shutting-down", "terminated"]:
                    inst.stop()
            print "Stopping slaves..."
            for inst in slave_nodes:
                if inst.state not in ["shutting-down", "terminated"]:
                    if inst.spot_instance_request_id:
                        inst.terminate()
                    else:
                        inst.stop()

    elif action == "start":
        (master_nodes, slave_nodes) = get_existing_cluster(conn, opts, cluster_name)
        print "Starting slaves..."
        for inst in slave_nodes:
            if inst.state not in ["shutting-down", "terminated"]:
                inst.start()
        print "Starting master..."
        for inst in master_nodes:
            if inst.state not in ["shutting-down", "terminated"]:
                inst.start()
        print_dns_urls(prefix=True)
        wait_for_cluster_state(
            conn=conn,
            opts=opts,
            cluster_instances=(master_nodes + slave_nodes),
            cluster_state='ssh-ready'
        )
        print_dns_urls(instances=master_nodes + slave_nodes)
        setup_cluster(conn, master_nodes, slave_nodes, opts, False)

    else:
        print >> stderr, "Invalid action: %s" % action
        sys.exit(1)


def print_dns_urls(instances=None, prefix=False):
    if instances:
        for inst in instances:
            print colors.OKBLUE + '[1]:http://%s' % inst.public_dns_name + colors.ENDC
            print colors.OKBLUE + '[2]:http://%s:8000/dashboard/experiment_list' \
                                 % inst.public_dns_name + colors.ENDC
    if prefix:
        print colors.OKBLUE + '[fyi]: The NEXT web interface will be available at [1]\n'\
                             + '[fyi]: The NEXT dashboard will be available at [2]\n'\
                             + '[fyi]: (URLs [1] and [2] available after cluster ssh-ready)'\
                             + '[fyi]: (also available through get-master command' + colors.ENDC

def main():
    try:
        real_main()
    except UsageError, e:
        print >> stderr, "\nError:\n", e
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig()
    main()
