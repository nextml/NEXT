FROM python:2
MAINTAINER Lalit Jain, lalitkumarj@gmail.com

# Install MongoDB and its tools
RUN \
	apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5 && \
    echo "deb http://repo.mongodb.org/apt/debian stretch/mongodb-org/3.6 main" | tee /etc/apt/sources.list.d/mongodb-org-3.6.list && \
    echo "deb http://ftp.debian.org/debian stretch-backports main" > /etc/apt/sources.list && \
	apt-get update -y && \
	apt-get install -y mongodb-org=3.6.11

# Install python dependencies for next_backend
ADD requirements.txt /requirements.txt
RUN pip install -U -r requirements.txt
