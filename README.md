# NEXT

[![gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/next-ml/Lobby?utm_source=share-link&utm_medium=link&utm_campaign=share-link)

**Documentation:** https://github.com/nextml/NEXT/wiki

**Website:** http://nextml.org

NEXT is a system that makes it *easy* to develop, evaluate, and apply active
learning.

Talk given by Lalit Jain that explains high level features of NEXT to active
learning researchers:

[![](https://github.com/nextml/NEXT/wiki/Figures/lalit-talk.png)](https://youtu.be/ESXgbZQ1ZTk?t=1732)
  
This readme contains a quick start to launch the NEXT system on EC2, and to
replicate and launch the experiments from the [NEXT
paper](http://www.cs.berkeley.edu/~kjamieson/resources/next.pdf). There are
more detailed launch instructions
[here](https://github.com/nextml/NEXT/wiki/NEXT-EC2-Launch-Tutorial).

For more information, in-depth tutorials, and API docs, we recommend visiting
our GitHub wiki [here](https://github.com/nextml/NEXT/wiki). You can contact us
at contact@nextml.org

We have an experimental AMI that can be used to run NEXT in a purely
application based rather than development environment. Included in the AMI is a
basic version of our frontend. The AMI is still highly experimental and we give
no guarantees on it being up to date with the current code.  For more info
please visit [here](https://github.com/kgjamieson/NEXT-psych).

## Testing
Run `py.test` from `NEXT/next`. Tests will be run from your local machine but
will ping an EC2 server to simulate a client.

Individual files can also be run with `py.test`. Running `py.test test_api.py`
will only run `test_api.py` and allow relative imports (which allows 
`from next.utils import timeit`).

`stdout` can be captured with the `-s` flag for `py.test`.

[pytest] is installable with `pip install pytest` and has a strict backwards
compatibility policy.

[pytest]:http://docs.pytest.org/en/latest/

### Getting the code

You can download the latest version of NEXT from github with the following
clone command:

```shell
$ git clone https://github.com/nextml/NEXT.git
```

We are actively working to develop and improve NEXT, but users should be aware of the following caveats: 

- NEXT currently supports only UNIX based OS (e.g. Windows compatibility is not
  yet available).
- An Amazon Web Services account is needed to launch NEXT on EC2; we have
  worked hard to make this process as simple as possible, at cost of ease of
  running the full NEXT stack on a local machine. We plan to make NEXT usable
  on a personal computer in the future.


### Launching NEXT on EC2

First, you must set your Amazon Web Services (AWS) account credentials as
enviornment variables. If you don't already have AWS account, you can follow
our AWS account quickstart
[here](https://github.com/nextml/NEXT/wiki/AWS-Account-Quickstart) or the
official AWS account set-up guide
[here](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html)
for an in-depth introduction. Make sure to have access to

* AWS access key id
* AWS secret access key
* Key Pair (pem file) 
 
> Make sure to note down the region that your key pair was made in. By default,
the script assumes the region is Oregon (us-west-2). If you choose to use a
different region, every time you use the ``next_ec2.py`` script, make sure to
specify the region ``--region=<region>`` (i.e., ``--region=us-west-2``). For
example, after  selecting the regions "Oregon," the region ``us-west-2`` is
specified on the EC2 dashboard. If another region is used, an ``--ami`` option
has to be included. For ease, we recommend using the Oregon region.

Export your AWS credentials as environment variables using:

```shell
$ export AWS_SECRET_ACCESS_KEY=[your_secret_aws_access_key_here]
$ export AWS_ACCESS_KEY_ID=[your_aws_access_key_id_here]
```

> Note that you'll need to use your `AWS_SECRET_ACCESS_KEY` and
`AWS_ACCESS_KEY_ID` again later, so save them in a secure place for convenient
reference later. 

Install the local python packages needed for NEXT:

```shell
$ cd NEXT
$ sudo pip install -r local_requirements.txt
```

Throughout the rest of this tutorial, we will be using the ``next_ec2.py``
startup script heavily. For more options and instructions, run 
`python next_ec2.py` without any arguments. Additionally, `python next_ec2.py -h`
will provide helper options.

For persistent data storage, we first need to create a bucket in AWS S3 using:

```shell
$ cd ec2
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] createbucket [cluster-name]
```

where:
- `[keypair]` is the name of your EC2 key pair
- `[key-file]` is the private key file for your key pair
- `[cluster-name]` is the custom name you create and assign to your cluster

This will print out another environment variable command `export
AWS_BUCKET_NAME=[bucket_uid]`. Copy and paste this command into your terminal. 

> You will also need to use your `bucket_uid` later, so save it in a file along
side your `AWS_SECRET_ACCESS_KEY` and `AWS_ACCESS_KEY_ID` for later reference.

Now you are ready to fire up the NEXT system using our `launch` command. This
command will create a new EC2 instance, pull the NEXT repository to that
instance, install all of the relevant Docker images, and finally run all Docker
containers. 

> WARNING: Users should note that this script launches a single `m3.large`
machine, the current default NEXT EC2 instance type. This instance type costs
$0.14 per hour to run. For more detailed EC2 pricing information, refer to this
AWS [page](http://aws.amazon.com/ec2/pricing/). You can change specify the
instance type you want to with the `--instance-type` option.

```shell
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] launch [cluster-name]
```

Once your terminal shows a stream of many multi-colored docker appliances, you
are successfully running the NEXT system! 

### Replicating NEXT adaptive learning experiments

Because NEXT aims to make it easy to reproduce empirical active learning
results, we provide a simple command to initialize the experiments performed in
[this  study](). 

First, in a new terminal, export your AWS credentials and use `get-master` to obtain your public EC2 DNS.
```
$ export AWS_BUCKET_NAME=[your_aws_bucket_name_here]
$ cd NEXT/ec2
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] get-master [cluster-name]
```
Then export this public EC2 DNS.

```shell
$ export NEXT_BACKEND_GLOBAL_HOST=[your_public_ec2_DNS_here]
$ export NEXT_BACKEND_GLOBAL_PORT=8000
```
Now you can execute `run_examples.py` to initialize and launch the NEXT experiments.

```shell
$ cd ../examples
$ python run_examples.py
```

Once initialized, this script will return a link that you can distribute
yourself or post as a HIT on [Mechanical
Turk](https://www.mturk.com/mturk/welcome). Visit:

`http://your_public_ec2_DNS_here:8000/query/query_page/query_page/[exp_uid]/[exp_key]` 

where `[exp_uid]` and `[exp_key]` are unique identifiers for each of the
respective Dueling Bandits Pure Exploration, Active Non-Metric Multidimensional
Scaling (MDS), and Tuple Bandits Pure Exploration experiments respectively. See
this [wiki
page](https://github.com/nextml/NEXT/wiki/Replicating-NEXT-Experiments#some-experiment-information)
for a little more information.

Navigate to the `strange_fruit_triplet` query link (the last one that printed
out to your terminal) and answer some questions! Doing so will provide the
system with data you can view and interact with in the next step.

### Accessing NEXT experiment results, dashboards, and data visualizations

You can access interactive experiment dashboards and data visualizations at by clicking experiments at:
- `http://your_public_ec2_DNS:8000/dashboard/experiment_list`

And obtain all logs for an experiment through our RESTful API, visit:
- `http://your_public_ec2_DNS:8000/api/experiment/[exp_uid]/[exp_key]/logs`

Where, again, `[exp_uid]` corresponds to the unique Experiment ID shown on the experiment dashboard pages.

If you'd like to backup your database to access your data later, refer to this [wiki](https://github.com/nextml/NEXT/wiki/NEXT-EC2-Launch-Tutorial#instance-teardown-and-database-backups) for detailed steps.

Finally, you can terminate your EC2 instance and shutdown NEXT using:

```shell
$ cd ../ec2
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] destroy [cluster-name]
```
