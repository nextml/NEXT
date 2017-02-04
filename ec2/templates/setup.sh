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
    boto \
    yaml

# tools for increased stability of docker volumes
apt-get install -y linux-image-extra-$(uname -r) aufs-tools  

# downloads and installs docker
# curl -sSL https://get.docker.com/ | sh  # only meant for testing >:[
# https://docs.docker.com/engine/installation/linux/ubuntu/
sudo apt-get update
sudo apt-get install -y curl linux-image-extra-$(uname -r) linux-image-extra-virtual
sudo apt-get install -y apt-transport-https ca-certificates
curl -fsSL https://yum.dockerproject.org/gpg | sudo apt-key add -
apt-key fingerprint 58118E89F3A912897C070ADBF76221572C52609D
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://apt.dockerproject.org/repo/ ubuntu-$(lsb_release -cs) main"
sudo apt-get update
sudo apt-get autoremove libltdl7
sudo sudo apt-get install -y docker-engine=1.10.3-0~trusty

# orchestrates docker containers
pip install docker-compose==1.10.0
