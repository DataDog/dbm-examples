
# aurora-postgres-iam

This is a Datadog Database Monitoring example that monitors an Aurora PostgreSQL Cluster with IAM authentication enabled.

## Prerequisites

* [AWS Account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)
* [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_prerequisites)
* [AWS VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)
* [Python 3.6+](https://www.python.org/downloads/)
* [Datadog API Key](https://app.datadoghq.com/account/settings#api)

This example assumes

* you have an AWS Account with a VPC. If you do not have a VPC, you can create one by following the [AWS VPC Getting Started Guide](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html).
* you have created an SSH key pair in the AWS region you are deploying to. If you do not have an SSH key pair, you can create one by following the [AWS EC2 Key Pairs Getting Started Guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair).
* you have a Datadog API Key. If you do not have a Datadog API Key, you can create one by following the [Datadog API Getting Started Guide](https://docs.datadoghq.com/account_management/api-app-keys/#add-an-api-key).

```bash

## Setup

Clone this repository

```bash
git clone https://github.com/DataDog/dbm-examples.git
```

Change directory to the `aws/aurora-postgres-iam` directory

```bash
cd aws/aurora-postgres-iam
```

Activate virtualenv

```bash
source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```bash
pip install -r requirements.txt
```

Set your Datadog API Key as an environment variable.

```bash
export DD_AP_KEY=<YOUR_DATADOG_API_KEY>
```

Replace `vpc_id` and `ssh_key_pair` in `app.py` with your VPC ID and SSH Key Pair name.

```python
AuroraPostgresIamStack(
    app,
    "auroa-postgres-iam",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    vpc_id='<YOUR-VPC-ID>',
    ssh_key_pair='<YOUR-SSH-KEY-PAIR>',
)
```

At this point you can now synthesize the CloudFormation template for this code.

```bash
cdk synth
```

Deploy the CloudFormation template.

```bash
cdk deploy
```
