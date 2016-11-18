The NEXT AMI on Amazon EC2 uses the two files in this directory to launch NEXT on startup.  `next.service` goes in 
`/lib/systemd/system/' and `next.sh` goes in `/usr/share/next/` (which will need to be created).  To enable launching of NEXT 
on startup, use `systemctl enable next`.  This requires the following packages to be installed:

* docker
* docker-compose
* python2.7
* pip

If these dependencies are satisfied, `next.sh` will run on startup and will pull the latest tagged commit of NEXT from the 
master branch of the NEXT repository and will run `/local/docker_up.sh` from that commit.
