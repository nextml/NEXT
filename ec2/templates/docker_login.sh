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

printf "######################################################\n\n Docker Environmental Variables Successfully Set\n\n Useful Docker Commands:\n    'docker-compose ps' : inspect Docker containers\n\n    'docker-compose up' : launch NEXT (append ' -d' to run containers in the background)\n\n    'docker-compose stop' : stop containers without losing data to change code\n\n    'docker rm -fv \$(docker ps -a -q)' : irrecovably delete all containers and their data\n\n    'docker rmi -f \$(docker images -a -q)' : delete all docker images ('docker-compose build' to rebuild)\n\n    'docker-compose logs' : live stream logs from all containers (use 'docker-compose logs [container_name]' to see single container's logs where [container_name] is the name of the container in the docker-compose.yml file)\n\n Tip: Getting strange errors when trying 'docker-compose up' AND you don't care about losing data? Remove the containers and try again.\n\n ######################################################\n"

/bin/bash -i