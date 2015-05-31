# NEXT

NEXT is a system that makes it *easy* to develop, evaluate, and apply active learning.

This readme contains the necessary steps to launch the NEXT system on EC2, and to replicate and launch the experiments from the [NEXT paper](). 

For new users, we recommend starting with the launch tutorial on our GitHub wiki [here](https://github.com/kgjamieson/NEXT/wiki/NEXT-EC2-Launch-Tutorial).

## Getting the code

You can download the latest version of NEXT from github with the following clone command:

```
$ git clone https://github.com/kgjamieson/NEXT.git
```

We are actively working to develop and improve NEXT, but users should be aware of the following caveats: 
- NEXT currently supports only UNIX based OS (e.g. Windows compatibility is not yet available).
- An Amazon Web Services account is needed to launch NEXT on EC2; we have worked hard to make this process as simple as possible, at cost of ease of running the full NEXT stack on a local machine.

## Launching NEXT on EC2

First, you must set your Amazon Web Services (AWS) account credentials as enviornment variables. If you don't already have AWS account, you can follow the AWS account set-up guide [here](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html).

Export your AWS credentials as environment variables using:
```
$ export AWS_SECRET_ACCESS_KEY=your_secret_aws_access_key_here
$ export AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
```

Install the local python packages needed for NEXT:
```
$ cd NEXT
$ sudo pip install -r local_requirements.txt
```

Now you are ready to fire up the NEXT system using our `launch` command. This command will create a new EC2 instance, pull the NEXT repository to that instance, install all of the relevant Docker images, and finally run all Docker containers. 

Users should note that this script launches a single `m3.large` machine, the current default NEXT EC2 instance type. This instance type costs $0.14 per hour to run. For more detailed EC2 pricing information, refer to this AWS [page](http://aws.amazon.com/ec2/pricing/).
```
$ cd ec2
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] launch [cluster-name]
```

where:
- `[keypair]` is the name of your EC2 key pair
- `[key-file]` is the private key file for your key pair
- `[cluster-name]` is the custom name you assign to your cluster

Once your terminal shows a stream of many multi-colored docker appliances, you are successfully running the NEXT system!

## Replicating NEXT adaptive learning experiments

Because NEXT aims to make it easy to reproduce empirical active learning results, we provide a simple command to initialize the experiments performed in [this  study](). 

First, in a new terminal, export your AWS credentials and use `get-master` to obtain your public EC2 DNS.
```
$ export AWS_SECRET_ACCESS_KEY=your_secret_aws_access_key_here
$ export AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] get-master [cluster-name]
```

Then export this public EC2 DNS.
```
$ export NEXT_FRONTEND_BASE_GLOBAL_HOST=your_public_ec2_DNS_here
$ export NEXT_FRONTEND_BASE_GLOBAL_PORT=8001
```

Now you can execute `run_examples.py` to initialize and launch the NEXT experiments.
```
$ cd ../examples
$ python run_examples.py
```
Once initialized, this script will return a link that you can distribute yourself or post as a HIT on [Mechanical Turk](https://www.mturk.com/mturk/welcome). Visit:

- `http://your_public_ec2_DNS_here:8000/query/query_page/StochasticDuelingBordaBanditsPureExploration/[exp_uid]/[exp_key]` for Pure Exploration for Dueling Bandits
- `http://your_public_ec2_DNS_here:8000/query/query_page/PoolBasedTripletMDS/[exp_uid]/[exp_key]` for Active Non-Metric Multidimensional Scaling (MDS)
- `http://your_public_ec2_DNS_here:8000/query/query_page/TupleBanditsPureExploration/[exp_uid]/[exp_key]` for Pure Exploration for Tuple Bandits

Navigate to the strange fruit query link and answer some questions! Doing so will provide the system with data you can view and interact with in the next step.

## Accessing NEXT experiment results, dashboards, and data visualizations

You can access interactive experiment dashboards and data visualizations at:
- `http://your_public_ec2_DNS:8000/dashboard/experiment_list`

And obtain all logs for an experiment through our RESTful API, visit:
- `http://your_public_ec2_DNS:8000/experiment/[exp_uid]/logs`

where `[exp_uid]` corresponds to the unique Experiment ID shown on the experiment dashboard pages.

Finally, you can terminate your EC2 instance and shutdown NEXT using:
```
$ python next_ec2.py --key-pair=[keypair] --identity-file=[key-file] destroy [cluster-name]
```
