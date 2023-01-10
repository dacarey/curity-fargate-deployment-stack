""" This is the main entry module of th cdk application """
#!/usr/bin/env python3
import os

import aws_cdk as cdk

from curity_fargate_cluster_stack.curity_fargate_cluster import CurityFargateCluster

def get_config():
    """get the stage identifier"""
    stage = app.node.try_get_context(key="stage")
    if not stage:
        raise LookupError(
            "The 'stage' variable missing on the cdk command."
            + "See cdk.json for available values, e.g. 'dw-dev','dw-sit', 'dw-uat'."
            + "Then pass these into you cdk command as '-c stage=dw-dev"
        )

    print(f"stage value is {stage}")

    stage_config = app.node.try_get_context(key=stage)
    if not stage_config:
        raise LookupError(
            f"The '{stage}' stage node is not configured in the cdk.json file"
        )

    print(f"stageConfig value is {stage_config}")
   


#
#  START HERE
# ==========================================================

app = cdk.App()

get_config()

CurityFargateCluster(
    app,
    "CurityFargateCluster",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.
    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */
    # env=cdk.Environment(account='123456789012', region='us-east-1'),
    # For more information, see
    #  https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

app.synth()
