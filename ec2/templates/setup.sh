#!/usr/bin/env bash

apt-get update

apt-get install -y python-pip

apt-get install -y linux-image-extra-$(uname -r) aufs-tools

curl -sSL https://get.docker.com/ubuntu/ | sh

easy_install -U pip

pip install requests==2.5.2

pip install docker-compose

# this comes 
	# http://www.speedguide.net/articles/linux-tweaking-121
	# from https://code.google.com/p/lusca-cache/issues/detail?id=89#c4
	# http://stackoverflow.com/questions/11190595/repeated-post-request-is-causing-error-socket-error-99-cannot-assign-reques
sysctl net.ipv4.tcp_tw_recycle=1
sysctl net.ipv4.tcp_tw_reuse=1