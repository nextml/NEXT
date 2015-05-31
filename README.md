# NEXT

NEXT is a system that makes it *easy* to develop, evaluate, and apply active learning.

This readme contains the necessary steps to launch the NEXT system on EC2, and to replicate and launch the experiments from the NEXT paper. For new users, we recommend starting with the launch tutorial on our GitHub wiki [here](https://github.com/kgjamieson/NEXT/wiki/NEXT-EC2-Launch-Tutorial).

## Getting the code

You can download the latest version of NEXT from github with the following clone command:

```
$ git clone https://github.com/kgjamieson/NEXT.git
```

## Launching NEXT on EC2

First, you must set your Amazon Web Services (AWS) account credentials as enviornment variables. If you don't already have AWS account, you can follow the AWS account set-up guide [here](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html).

Export your AWS credentials as environment variables using:
```
$ export AWS_SECRET_ACCESS_KEY=your_secret_aws_access_key_here
$ export AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
```

Now you are ready to fire up the NEXT system using our launch command. This command will create a new EC2 instance, pull the NEXT repository to that instance, install all of the relevant Docker images, and finally run all Docker containers.

```
$ cd NEXT/ec2
$ sudo pip install boto
$ python next_ec2.py --key-pair=<keypair> --identity-file=<key-file> launch <cluster-name>
```

where:
- `<keypair>` is the name of your EC2 key pair
- `<key-file>` is the private key file for your key pair
- `<cluster-name>` is the custom name you assign to your cluster

Once your terminal shows a stream of many multi-colored docker appliances, you are now running the NEXT system!

## Replicating NEXT adaptive learning experiments

Because NEXT aims to make it easy to reproduce empirical active learning results, we provide a one-line command to initialize the experiments performed in [this  study](). 

First, in a new terminal, export your AWS credentials and use `get-master` to obtain your public EC2 DNS.
```
$ export AWS_SECRET_ACCESS_KEY=your_secret_aws_access_key_here
$ export AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
$ cd NEXT/ec2
$ python next_ec2.py --key-pair=<keypair> --identity-file=<key-file> get-master <cluster-name>
```

Then export this public EC2 DNS and install the python requests library.
```
$ export NEXT_FRONTEND_BASE_GLOBAL_HOST=your_public_ec2_DNS_here
$ export NEXT_FRONTEND_BASE_GLOBAL_PORT=8001
$ sudo pip install requests
```

Now you can execute `run_examples.py` to initialize and launch the NEXT experiments.
```
$ cd NEXT/examples
$ python run_examples.py
```
Once initialized, this script will return a link that you can distribute yourself or post as a HIT on Mechanical Turk. Visit:

- `http://your_public_ec2_DNS_here:8000/query/query_page/StochasticDuelingBordaBanditsPureExploration/<exp_uid>/<exp_key>` for Pure Exploration for Dueling Bandits
- `http://your_public_ec2_DNS_here:8000/query/query_page/PoolBasedTripletMDS/<exp_uid>/<exp_key>` for Active Non-Metric Multidimensional Scaling (MDS)
- `http://your_public_ec2_DNS_here:8000/query/query_page/TupleBanditsPureExploration/<exp_uid>/<exp_key>` for Pure Exploration for Tuple Bandits

## Accessing NEXT experiment results, dashboards, and data visualizations

You can access interactive experiment dashboards and data visualizations at:
- `http://your_public_ec2_DNS:8000/dashboard/experiment_list`

And obtain all participant logs for an experiment through our RESTful API via cURL using:
```
$ curl -X GET http://your_public_ec2_DNS:8000/experiment/<exp_uid>/logs
```
where `<exp_uid>` corresponds to the unique Experiment ID shown on the experiment dashboard pages.
