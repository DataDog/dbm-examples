#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aurora_postgres_iam.aurora_postgres_iam_stack import AuroraPostgresIamStack


app = cdk.App()
AuroraPostgresIamStack(
    app,
    "auroa-postgres-iam",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    vpc_id='<YOUR-VPC-ID>',  # replace with your VPC ID
    ssh_key_pair='<YOUR-SSH-KEY-PAIR>',  # replace with your SSH key pair
)

app.synth()


