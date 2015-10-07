#!/usr/bin/env bash

cd /usr/local/next-discovery

export NEXT_BACKEND_GLOBAL_PORT=8192
export AWS_ACCESS_ID=None
export AWS_SECRET_ACCESS_KEY=None
export NEXT_FRONTEND_GLOBAL_PORT=8002
export NEXT_FRONTEND_GLOBAL_HOST=localhost
export MASTER_LIST=localhost
export AWS_BUCKET_NAME=next-database-backups
export ACTIVE_MASTER=localhost
export SLAVE_LIST=
export NEXT_BACKEND_GLOBAL_HOST=localhost


# this comes 
	# http://www.speedguide.net/articles/linux-tweaking-121
	# from https://code.google.com/p/lusca-cache/issues/detail?id=89#c4
	# http://stackoverflow.com/questions/11190595/repeated-post-request-is-causing-error-socket-error-99-cannot-assign-reques
sysctl net.ipv4.tcp_tw_recycle=1
sysctl net.ipv4.tcp_tw_reuse=1

/bin/bash -i