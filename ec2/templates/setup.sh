#!/usr/bin/env bash

apt-get update

# install pip and some libraries (for convenience and test scripts)
apt-get install -y \
    python \
    python-dev \
    python-distribute \
    python-pip \
    python-numpy \
    python-scipy \
    git

# python libraries (for convenience and test scripts)
pip install \
	requests==2.5.2 \
	boto

# tools for increased stability of docker volumes
apt-get install -y linux-image-extra-$(uname -r) aufs-tools  

# downloads and installs docker
curl -sSL https://get.docker.com/ubuntu/ | sh

# orchestrates docker containers
pip install docker-compose