sudo apt-get install git
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-precise main" | sudo tee -a /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get instal linux-image-extra-$(uname -r)

sudo apt-get install docker
sudo apt-get install docker-engine
pip install docker-compose

# Start the docker daemon
# sudo service docker start
# possibly sudo service docker restart

# Verify that docker is installed correctly
# sudo docker run hello-world

# docker-compose.yml.pre
    # comment out GIT_HASH on line 45
# run sudo ./docker-compose localhost [NEXT filepath]

# sudo docker-compose up
