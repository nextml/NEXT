We provide two interfaces for launching an experiment:

1. Using `launch.py`. This is the recommended method.
2. Using `launch_experiment.py`.

Example usage of `launch.py`:

``` shell
> cd ~/Developer/NEXT/examples/
> python launch.py strange_fruit_triplet/init.yaml strange_fruit_triplet/strangefruit30.zip
```

where an examples of both files (`init.yaml` and `strangefruit30.zip`) are in
`strange_fruit_triplet`. The zip file contains images of all the targets and
`init.yaml` contains arguments to initialize the experiment with.

The YAML file can also specify the targets. For an example of what keys should
be present, look at `cartoon_dueling/init.yaml`. This can be used with
`localhost` and hosting the targets with off a local server (example given in
`NEXT/local`.

If a ZIP file is included, this method does send your AWS credentials over the
WiFi network.  This is not secure and the most likely failure point is public
WiFi where these can be sniffed. **We do not recommend launching experiments
using public WiFi**. If this *must* be done, we recommend using a VPN to
connect to your home/office/university network.

----

This scripts in this directory launch an experiment on a machine already
running NEXT whose hostname is specified in the environment variable
`NEXT_BACKEND_GLOBAL_HOST`.  For example,
`examples/strange_fruit_triplet/experiment_tripley.py` launches a triplet
experiment the machine whose hostname is specified in
`NEXT_BACKEND_GLOBAL_HOST`.

Typically, `NEXT_BACKEND_GLOBAL_HOST` is a Amazon EC2 public DNS.

These scripts upload to Amazon S3. To do this, other Amazon AWS environment
variables are needed, `AWS_BUCKET_NAME`, `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY`.  For setting up other Amazon AWS environment
variables, see the documentation at [AWS Account Quickstart].

It is possible to change these examples to launch on a local machine but this
has not been tested.

[AWS Account Quickstart]:https://github.com/nextml/NEXT/wiki/NEXT-Reference:-AWS-Account-Quickstart
