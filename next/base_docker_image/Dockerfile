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
    python-matplotlib 

# Install MongoDB and its tools
RUN \
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10 && \
  echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' > /etc/apt/sources.list.d/mongodb.list && \
  apt-get update && \
  apt-get install -y mongodb-org && \
  rm -rf /var/lib/apt/lists/*

# Install python dependencies for next_backend
ADD requirements.txt /requirements.txt
RUN pip install -U -r requirements.txt

