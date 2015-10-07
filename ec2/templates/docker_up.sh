#!/usr/bin/env bash

[ $(getent group docker) ] || groupadd docker
sudo gpasswd -a $(whoami) docker

cd /usr/local/next-discovery

{{ environment_variables }}

# this comes 
	# http://www.speedguide.net/articles/linux-tweaking-121
	# from https://code.google.com/p/lusca-cache/issues/detail?id=89#c4
	# http://stackoverflow.com/questions/11190595/repeated-post-request-is-causing-error-socket-error-99-cannot-assign-reques
sysctl net.ipv4.tcp_tw_recycle=1
sysctl net.ipv4.tcp_tw_reuse=1

docker-compose stop

docker-compose up