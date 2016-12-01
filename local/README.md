# Running NEXT locally
We provide this structure to run NEXT locally (which could be necessary if data
private).

## Dependencies

To run NEXT locally, you need a machine with the following things installed:

```
docker
docker-compose
python2.7
```

It is assumed you have python2.7 by default on linux.

`docker` can be installed via the [Docker install guide]. `docker-compose` can
be installed via `pip install docker-compose`.

### Using macOS
If using macOS/OS X, download [Docker for Mac], not [Docker Toolbox]. It
provides an easier interface to get started.

[Docker for Mac]:https://docs.docker.com/engine/installation/mac/#/docker-for-mac

[Docker install guide]:https://docs.docker.com/v1.8/installation/

## Starting the backend

First clone this repository and navigate to the `NEXT/local/` directory.  

To start up the NEXT backend, run `./docker_up.sh [host]` where `host`
is the IP or hostname of the machine running the backend.  You may
optionally provide a path to the repo if you are running the
`docker_up` script from a different directory.  For example:

```
./docker_up.sh [host] [/path/to/NEXT]
```

where the relative path to NEXT is optional and host is not. A typical
command is

```
./docker_up.sh
```

which assumes the directory `NEXT` is located at `../` when cd'd to `local`.

## Starting example experiment

To set up an experiment, you need the target files hosted somewhere,
and to have a manifest file consisting of JSON specifying filename:url
pairs.  For an example, see `NEXT/local/strangefruit30.json`, which
assumes the files are served hosted on `localhost:8999`.

Hosting the images on `localhost:8999` can be achieved by running
`python -m SimpleHTTPServer 8999` in the directory that contains the images.

Next you will need to make `next_worker_startup.sh` executable. It is located in `NEXT/next/broker/` directory. The command to make the file executable is

```bash
$ chmod +x next_worker_startup.sh
```

An example is provided in `experiment_triplet.py`. In
the `strangefruit30` example, unzip `strangefruit30.zip` and run
`python -m SimpleHTTPServer 8999` from the `strangefruit30` directory.

``` bash
$ python experiment_triplet.py
```

This `experiment_triplet.py` file is nearly identical to the files in
`examples/` as the dictionaries to initialize an experiment are constant. The
only difference is launching on EC2 vs. launching locally which manifests
itself on the last line which calls `launch_experiment.py`.

## Starting new experiment
Two things are needed to run all the examples in `examples/`:

1. Copy the files from `examples/` and modify the `launch_experiment` line at
   the end to match `local/experiment_triplet.py`
2. (optional) If you're running an experiment with non-numeric targets (which
   we use to test), you'll have to host the images on some URL. A process for
   hosting them on `localhost` is described above.

Once this is set up, you can start the experiment with 

```
python my_experiment.py path/to/my_experiment.json
```

[Docker Toolbox]:https://www.docker.com/products/docker-toolbox
