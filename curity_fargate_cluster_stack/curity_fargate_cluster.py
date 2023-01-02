from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
)
from constructs import Construct
from curity_fargate_cluster_stack import (
    bastion_deployment as bastianDepl,
    curity_fargate_service as curityServiceFactory,
)


#
#  This is our MAIN Entry Point.  We are called by app.py
class CurityFargateCluster(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #
        #  Lookup the VPC as this is assumed to have been pre-created for us
        vpc = self.lookupVPC()

        #
        #   Create an ECS Cluster inside the VPC
        curity_cluster = self.createClusterFromVPC(vpc)

        curityAdminService = curityServiceFactory.CurityFargateService(
            self, curity_cluster, admin=True
        )
        CfnOutput(
            self,
            "curityService",
            value=curityAdminService.curity_service.to_string()
        )
        CfnOutput(
            self,
            "CurityService Task Definition.  Task Role",
            value=curityAdminService.curity_service.task_definition.task_role.to_string(),
        )

        bastionDeployment = bastianDepl.BastionDeployment(self, vpc)
        CfnOutput(
            self,
            "bastionInstance",
            value=bastionDeployment.instance.instance_id
        )

        curityAdminService.curity_service.service.connections.allow_from(
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
