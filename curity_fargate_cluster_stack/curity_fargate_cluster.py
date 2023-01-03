from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
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
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #
        #  1/ Lookup the VPC as this is assumed to have been pre-created for us
        # =====================================================================
        vpc = self.lookupVPC()

        #
        # 2/  Create an ECS Cluster inside the VPC
        # This will also create a private Cloud Map namespace
        # to allow the services to discover each other
        # =====================================================================
        curity_cluster = self.createClusterFromVPC(vpc)

        #
        # 3/ Create our Curity services
        # -  The Admin Service is a simple vanilla Fargate service
        #    with a single admin task.
        # -  The Runtime Service is a load-balanced Fargate service
        #    with multiple tasks
        # =====================================================================

        curityAdminService = adminServiceFactory.CurityAdminService(
            self, curity_cluster, adminService=True
        )
        CfnOutput(
            self,
            "curityAdminService",
            value=curityAdminService.curity_service.to_string()
        )
        CfnOutput(
            self,
            "CurityAdminService Task Definition.  Task Role",
            value=curityAdminService.curity_service.task_definition.task_role.to_string(),
        )

        curityRuntimeService = runtimeServiceFactory.CurityRuntimeService(
            self, curity_cluster, adminService=False
        )
        CfnOutput(
            self,
            "curityRuntimeService",
            value=curityRuntimeService.curity_service.to_string()
        )
        CfnOutput(
            self,
            "CurityRuntimeService Task Definition.  Task Role",
            value=curityRuntimeService.curity_service.task_definition.task_role.to_string(),
        )

        #
        # 3a/ We need to ensure the tasks in the Runtime Services
        #     can comminicate to the master task in the Admin Service
        # =====================================================================

        curityAdminService.curity_service.connections.allow_from(
            curityRuntimeService.curity_service.service,
            ec2.Port.tcp(6789),
            "Allow the Curity Runtimes Tasks to communicate with the Curity Admin service on the Cluster Communication Port",
        )

        #
        # 4/ Create a bastion EC2 instance for support purposes only
        #   This will allow us to create an SSM tunnel to:-
        #   - Access the Curity Web Admin locally, without requiring
        #     a VPN tobe setup.
        #   - General Debug diagnosis
        bastionDeployment = bastianDepl.BastionDeployment(self, vpc)
        CfnOutput(
            self,
            "bastionInstance",
            value=bastionDeployment.instance.instance_id
        )

        curityAdminService.curity_service.connections.allow_from(
            bastionDeployment.instance,
            ec2.Port.all_tcp(),
            "Bastion access to the Fargate Service",
        )

        curityRuntimeService.curity_service.service.connections.allow_from(
            bastionDeployment.instance,
            ec2.Port.all_tcp(),
            "Bastion access to the Fargate Service",
        )

    #
    #  lookup the VPC -  Otherwise raise an exception
    # ==================================================================
    def lookupVPC(self):
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="curityvpc")
        if not vpc:
            raise Exception("Failed to find VPC: 'curityvpc'")
        return vpc

    #
    #   create an ECS Cluster inside the supplied VPC
    # =========================================================================
    def createClusterFromVPC(self, vpc):
        curity_cluster = ecs.Cluster(
            self,
            "curityvpcid",
            vpc=vpc,
            cluster_name="curity-cluster"
        )

        # Adding service discovery namespace to cluster
        curity_cluster.add_default_cloud_map_namespace(
           name="curity"
        )

        return curity_cluster
