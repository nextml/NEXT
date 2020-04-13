#!/usr/bin/env bash


sudo apt-get update

# install pip and some libraries (for convenience and test scripts)
sudo apt-get install -y \
    python \
    python-dev \
    python-distribute \
    python-yaml \
    python-pip \
    python-numpy \
    python-scipy \
    git

sudo pip install -U pip
sudo pip install --upgrade setuptools
# python libraries (for convenience and test scripts)
sudo pip install boto

# tools for increased stability of docker volumes
sudo apt-get install -y linux-image-extra-$(uname -r) aufs-tools


sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common


#sudo apt-get update

sudo apt-get install -y curl linux-image-extra-$(uname -r) linux-image-extra-virtual


curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

sudo apt-key fingerprint 0EBFCD88
#sudo apt-get install -y software-properties-common

sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
#sudo apt-get install linux-generic-lts-xenial
sudo apt-get update
#sudo apt-get autoremove libltdl7
#sudo sudo apt-get install -y docker-engine=1.10.3-0~trusty
sudo apt-get install -y docker-ce
# orchestrates docker containers
#pip install docker-compose==1.10.0
#sudo pip install docker-compose
sudo docker version
sudo curl -L "https://github.com/docker/compose/releases/download/1.25.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
