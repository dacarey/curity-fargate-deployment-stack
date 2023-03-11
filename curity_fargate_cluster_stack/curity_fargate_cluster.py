"""This module provides the CurityFargateCluster class."""
from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_s3_assets as s3_assets,
    aws_servicediscovery as sd
)
from constructs import Construct
from curity_fargate_cluster_stack import (
    admin_fargate_service as adminServiceFactory,
    runtime_fargate_service as runtimeServiceFactory,
    bastion_deployment as bastianDepl,
)


#
#  This is our MAIN Entry Point.  We are called by app.py
class CurityFargateCluster(Stack):
    """This class creates a Fargate Cluster for a Curity Cluster consisting
    of an Admin Service and a Runtime Service."""

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CfnOutput(
            self,
            "Curity AWS configurable environment settings",
            value=str(config),
        )

        #
        #  1/ Lookup the VPC as this is assumed to have been pre-created for us
        # =====================================================================
        vpc = self.lookup_vpc(config)

        #
        #  2/ Sync the envfile if it is present
        # =====================================================================
        env_file = config.get("envfile")
        if env_file:
            config["envfile_asset"] = self.sync_envfile( env_file)

        #
        # 3/  Create an ECS Cluster inside the VPC
        # This will also create a private Cloud Map namespace
        # to allow the services to discover each other
        # =====================================================================
        curity_cluster = self.create_cluster_from_vpc(vpc)

        #
        # 4/ Create our Curity services
        # -  The Admin Service is a simple vanilla Fargate service
        #    with a single admin task.
        # -  The Runtime Service is a load-balanced Fargate service
        #    with multiple tasks
        # =====================================================================

        curity_admin_service = adminServiceFactory.CurityAdminService(
            self, curity_cluster, config, admin_service=True,
        )
        CfnOutput(
            self,
            "curityAdminService",
            value=curity_admin_service.curity_service.to_string(),
        )
        CfnOutput(
            self,
            "CurityAdminService Task Definition.  Task Role",
            value=curity_admin_service.curity_service.task_definition.task_role.to_string(),
        )

        curity_runtime_service = runtimeServiceFactory.CurityRuntimeService(
            self, curity_cluster, config
        )
        CfnOutput(
            self,
            "curityRuntimeService",
            value=curity_runtime_service.curity_service.to_string(),
        )
        CfnOutput(
            self,
            "CurityRuntimeService Task Definition.  Task Role",
            value=curity_runtime_service.curity_service.task_definition.task_role.to_string(),
        )

        #
        # 3a/ We need to ensure the tasks in the Runtime Services
        #     can comminicate to the master task in the Admin Service
        # =====================================================================

        curity_admin_service.curity_service.connections.allow_from(
            curity_runtime_service.curity_service.service,
            ec2.Port.tcp(6789),
            "Allow the Curity Runtimes Tasks to communicate with the Curity Admin "
            "service on the Cluster Communication Port",
        )

        #
        # 4/ Create a bastion EC2 instance for support purposes only
        #   This will allow us to create an SSM tunnel to:-
        #   - Access the Curity Web Admin locally, via an SSM tunnel
        #      ( means no VPN is required)
        #   - See the ssm.sh script on how to set this up
        #
        bastion_deployment = bastianDepl.BastionDeployment(self, vpc)
        bastion_instance_id=bastion_deployment.instance.instance_id
        CfnOutput(
            self, "bastionInstance", value=bastion_instance_id
        )
        bastion_ipaddress=bastion_deployment.instance.instance_private_ip
        CfnOutput(
            self, "bastionInstance IP", value=bastion_ipaddress
        )

        curity_admin_service.curity_service.connections.allow_from(
            bastion_deployment.instance,
            ec2.Port.all_tcp(),
            "Bastion access to the Fargate Service",
        )

        curity_runtime_service.curity_service.service.connections.allow_from(
            bastion_deployment.instance,
            ec2.Port.all_tcp(),
            "Bastion access to the Fargate Service",
        )

        # Add the EC2 instance to the CloudMap namespace
        service = self.namespace.create_service("BastionService",
            dns_record_type=sd.DnsRecordType.A,
            dns_ttl=Duration.seconds(60)
        )

        # Register the EC2 instance with the service
        service.register_ip_instance("BastionInstance",
                                     ipv4=bastion_ipaddress)

    #
    #  lookup the VPC -  Otherwise raise an exception
    # ==================================================================
    def lookup_vpc(self, config):
        """lookup an existing vpc based on its name"""
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=config.get("vpcname"))
        if not vpc:
            raise Exception(f"Failed to find VPC: '${config.get('vpcname')}'")
        return vpc

    #
    #   create an ECS Cluster inside the supplied VPC
    # =========================================================================
    def create_cluster_from_vpc(self, vpc):
        """create an ec2 cluster and associate a cloudmap namespace
        ready for any services to use"""
        curity_cluster = ecs.Cluster(
            self, "curityvpcid", vpc=vpc, cluster_name="curity-cluster"
        )

        # Adding service discovery namespace to cluster
        self.namespace = curity_cluster.add_default_cloud_map_namespace(name="curity")

        return curity_cluster

    #
    #  sync the env file to an S3 bucket  -  Otherwise raise an exception
    # ==================================================================
    def sync_envfile(self, env_file):
        """This class contains the CDK code to synchronize our Curity
        environment file to an S3 bucket so that it can be referenced by the
        Fargate service classes."""

        # Create an Asset from the local file and upload it to the S3 bucket if it has changed
        asset = s3_assets.Asset(self, "CurityEnvFile", path=env_file)

        CfnOutput(self, "S3BucketName", value=asset.s3_bucket_name)
        CfnOutput(self, "S3ObjectKey", value=asset.s3_object_key)
        CfnOutput(self, "S3HttpURL", value=asset.http_url)

        return asset
