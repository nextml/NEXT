# Running NEXT locally

This has only been tested on Linux. This assumes that all ports are open and
the all connections can be made.

## Dependencies

To run NEXT locally, you need a machine with the following things installed:

```
docker
docker-compose
python2.7
```

The dependencies can be installed with `sudo sh requirements.sh`. This script
installs docker (and various docker tools).

It is assumed you have python2.7 by default on linux.

## Starting the backend

First clone this repository and navigate to the `NEXT/local/` directory.  

To start up the NEXT backend, run `./docker_up.sh [host]` where `host`
is the IP or hostname of the machine running the backend.  You may
optionally provide a path to the repo if you are running the
`docker_up` script from a different directory.  For example:

```
sudo ./docker_up.sh [host] /home/username/NEXT
```

where the relative path to NEXT is optional and host is not. A typical
command is

```
sudo ./docker_up.sh localhost
```

which assumes the directory `NEXT` is located at `../` when cd'd to `local`.

## Starting an experiment

To set up an experiment, you need the target files hosted somewhere,
and to have a manifest file consisting of JSON specifying filename:url
pairs.  For an example, see `/local/strangefruit30.manifest`, which
assumes the files are served hosted on `example.com:8999`.  

You will also need a python file analogous to the provided example
`experiment_triplet.py` which sets up the config parameters for the
particular experiment (what algorithms to use, etc.).

Once this is set up, you can start the experiment with 

```
python my_experiment.py path/to/my_experiment.manifest
```
