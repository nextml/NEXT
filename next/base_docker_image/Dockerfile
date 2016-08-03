FROM ubuntu:14.04
MAINTAINER Lalit Jain, lalitkumarj@gmail.com
# Install basic applications
RUN apt-get update && apt-get install -y \
    python \
    python-dev \
    python-distribute \ 
    python-pip \
    python-numpy \
    python-scipy \
    python-gevent \
    python-matplotlib \ 
    python-ply \
    numactl 

# Install MongoDB and its tools
RUN \
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927 && \
  echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" > /etc/apt/sources.list.d/mongodb-org-3.2.list && \
  apt-get update && \
  apt-get install -y mongodb-org && \
  rm -rf /var/lib/apt/lists/*

# Install python dependencies for next_backend
ADD requirements.txt /requirements.txt
RUN pip install -U -r requirements.txt

