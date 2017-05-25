FROM ubuntu:14.04
MAINTAINER Lalit Jain, lalitkumarj@gmail.com
# Install basic applications
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-pandas \
    python3-matplotlib \
    python3-ply \
    numactl

# Put in place because ran into bug with pip (!)
RUN python3 -m pip install -U pip

# Install MongoDB and its tools
RUN \
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927 && \
  echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" > /etc/apt/sources.list.d/mongodb-org-3.2.list && \
  apt-get update && \
  apt-get install -y mongodb-org && \
  rm -rf /var/lib/apt/lists/*

# Install python dependencies for next_backend
ADD requirements.txt /requirements.txt
RUN pip3 install -U -r requirements.txt

