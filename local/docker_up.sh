#!/usr/bin/env bash

HOST=$1
export NEXT_BACKEND_GLOBAL_PORT=8000
export AWS_ACCESS_ID=None
export AWS_SECRET_ACCESS_KEY=None
export NEXT_FRONTEND_GLOBAL_PORT=8002
export NEXT_FRONTEND_GLOBAL_HOST=$HOST
export MASTER_LIST=$HOST
export AWS_BUCKET_NAME=next-database-backups
export ACTIVE_MASTER=$HOST
export SLAVE_LIST=
export NEXT_BACKEND_GLOBAL_HOST=$HOST


# this comes 
	# http://www.speedguide.net/articles/linux-tweaking-121
	# from https://code.google.com/p/lusca-cache/issues/detail?id=89#c4
	# http://stackoverflow.com/questions/11190595/repeated-post-request-is-causing-error-socket-error-99-cannot-assign-reques
sudo sysctl net.ipv4.tcp_tw_recycle=1
sudo sysctl net.ipv4.tcp_tw_reuse=1

function abspath() {
    if [ -d "$1" ]; then
        echo "$(cd "$1"; pwd)"
    elif [ -f "$1" ]; then
        # file
        if [[ $1 == */* ]]; then
            echo "$(cd "${1%/*}"; pwd)/${1##*/}"
        else
            echo "$(pwd)/$1"
        fi
    fi
}

if [ "$#" -lt 2 ]; then 
    dir=$(abspath ..);
    echo "No path to NEXT provided.  Assuming ../";
else
    dir=$(abspath $2);
    echo "Using $1 as path to NEXT.";
fi

cp -f docker-compose.yml.pre docker-compose.yml
sed -i 's|{{NEXT_DIR}}|'"$dir"'|g' docker-compose.yml

docker-compose stop

docker-compose up
