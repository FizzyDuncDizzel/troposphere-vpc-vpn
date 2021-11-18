# troposphere-vpc-vpn for TOP

## Steps for use

This repo is here to help you learn both Runway and how it handles deployments of cloudformation into AWS via cfngin. This repo is configured using the `Git branches` environment and file structure. This repo only works with the `common` environment, of which the `master` git branch is tied to.

### Prep your env

1. You must first edit your "customer" name in every environment file to be unique. Stacker (which is the tool being executed by runway), uploads your cloudformation to S3 under a S3 bucket it creates named `stacker-<customer>-<env>`. As a result, everyone *MUST* change the customer name in every environment file before proceeding.
Files to change are:
* core.cfn/common-us-west-2.env

2. Using pipenv install the modules locally on your machine using `pipenv sync`

3. Install the Chef DK (should already have) - this is needed by one of the VPN cookbook packaging

### VPN Prep

We are making use of local auth using Linux PAM. An encrypted password can be generated using the following command which prompts for your password and then spits out the encrypted version of it that can be inserted into `core.cfn/cookbooks/top-launch-demo_vpc/recipes/pam.rb` (see notes within that file).

```
pip install passlib
python -c "from __future__ import print_function; from builtins import input; from passlib.hash import sha512_crypt; print(sha512_crypt.encrypt(input('clear-text password: ')))"
```

### Deploy your stacks

After you have prepped your environment, you may proceed with a runway deployment.

`make deploy`

The above command will execute `runway deploy` in a python virtual environment.

### VPN test

If the VPN server was successfully configured through chef it'll drop a `client.ovpn` file over in the chef data bucket. Retrieve and use to connect using your favorite openvpn compatible VPN client (tunnelblick/openvpn client/viscosity)


### Launch something in the VPC

Copy over your img-mgr.tf into this runway project, add it as a module. Refactor to make use of cloudformation data [aws-cloudformation-stack](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudformation_stack) to get the necessary outputs for img-mgr including (but maybe not limited to):

* vpc-id
* subnets
* all-sg (this is the sg we add to resources that we want the VPN to have access to)
* AZ (it's possible that some work needs to be done here)

For your ec2 instances assign an ssh key, you'll be making use of this to directly access the machine. Modify the ASG to attach the `AllSecurityGroup` to your img-mgr ec2 instances.

Deploy only the `dev` env within your VPC.

Connect to your VPN, then ssh directly into one of the img mgr machines using it's private IP address.

### Tear Down / The "I want it to go away" section

Runway can tear down/destory your whole stack.  Runway allows for you to do this via the cli, that we have prepackaged a MakeFile that does this for you:

`make destroy`
