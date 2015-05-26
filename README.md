# NEXT

## Getting the code

You can download the latest version of NEXT from github with the following clone command:

```
$ git clone https://github.com/kgjamieson/NEXT.git
```

## Launching NEXT on EC2

First, you must set your Amazon Web Services (AWS) account credentials as enviornment variables. If you don't already have AWS account, you can follow the AWS account set-up guide [here](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html).

Export your AWS credentials as environment variables using:
```
$ export AWS_SECRET_ACCESS_KEY = your_secret_aws_access_key_here
$ export AWS_ACCESS_KEY_ID = your_aws_access_key_id_here
```

Now you are ready to fire up the NEXT system using our launch command. This command will create a new EC2 instance, pull the NEXT repository to that instance, install all of the relevant Docker images, and finally run all Docker containers.

```
$ cd NEXT/ec2
$ python next_ec2.py --key-pair=<keypair> --identity-file=<key-file> launch <cluster-name>
```

For example, if you would like to fire up a c3.8xlarge instance type, after filling in your credentials, your launch command will look something like this:

```
$ python next_ec2.py --key-pair=my_aws_key --identity-file=~/Downloads/my_aws_key.pem \
--instance-type=c3.8xlarge launch next_test_instance
```
Once your terminal shows a stream of many multi-colored docker appliances, *wallah*, you are now running the NEXT system!

## Replicating NEXT adaptive learning experiments

Because NEXT aims to make it easy to reproduce empirical active learning results, we provide a one-line command to initialize the experiments performed in [this  study](). 
```
$ cd NEXT/examples
$ python run_examples.py
```
Once initialized, this script will return a link that you can distribute yourself or post as a HIT on Mechanical Turk. Visit:

- `http://your_public_ec2_DNS:8001/query/cartoon_dueling` for Pure Exploration for Dueling Bandits
- `http://your_public_ec2_DNS:8001/query/cartoon_triplet` for Active Non-Metric Multidimensional Scaling
- `http://your_public_ec2_DNS:8001/query/cartoon_tuple` for Pure Exploration for Tuple Bandits

## View experiment results, dashboards, and data visualizations

You can access interactive experiment dashboards and data visualizations at:
`http://your_public_ec2_DNS:8000/dashboard/experiment_list`

And obtain all participant logs for an experiment through our RESTful API via cURL using:
```
$ curl -X GET http://your_public_ec2_DNS:8000/experiment/<exp_uid>/logs
```
where `<exp_uid>` corresponds to the unique Experiment ID shown on the experiment dashboard pages.
