This scripts in this directory launch an experiment on a machine already
running NEXT whose hostname is specified in the environment variable
`NEXT_BACKEND_GLOBAL_HOST`.  For example,
`examples/strange_fruit_triplet/experiment_tripley.py` launches a triplet
experiment the machine whose hostname is specified in
`NEXT_BACKEND_GLOBAL_HOST`.

Typically, `NEXT_BACKEND_GLOBAL_HOST` is a Amazon EC2 public DNS.

These scripts upload to Amazon S3. To do this, other Amazon AWS environment
variables are needed, `AWS_BUCKET_NAME, `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY`.  For setting up other Amazon AWS environment
variables, see the documentation at [AWS Account Quickstart].

It is possible to change these examples to launch on a local machine but this
has not been tested.

[AWS Account Quickstart]:https://github.com/nextml/NEXT/wiki/NEXT-Reference:-AWS-Account-Quickstart
