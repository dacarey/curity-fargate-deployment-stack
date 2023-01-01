from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    Tags
)


#
#
#  This code is based on this GitHUB repository
#  https://github.com/aws-samples/aws-cdk-examples/tree/master/python/ec2/instance
class BastionDeployment:
    def __init__(self, construct, vpc):
        # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
        )

        # Instance Role and SSM Managed Policy
        role = iam.Role(
            construct, "InstanceSSM",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )

        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )

        # Instance
        self.instance = ec2.Instance(
            construct,
            "Instance",
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=amzn_linux,
            vpc=vpc,
            role=role,
        )

        Tags.of(self.instance).add("curity-ec2-type", "curity-bastion")
