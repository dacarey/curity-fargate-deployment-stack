""" This module contains the class for the Curity Admin Service """
from aws_cdk import (
    aws_ecs as ecs,
)
from curity_fargate_cluster_stack.base_fargate_service import (
    BaseFargateService
)


class CurityAdminService(BaseFargateService):
    """ This class creates and deploys the Curity Admin node within the ECS Cluster """
    def __init__(self, construct, curity_cluster, config, admin_service):
        #
        # Prepare the Container and associated ECS Task
        # ====================================================================
        curity_image = CurityAdminService.choose_docker_admin_image(construct)

        admin_task_definition = self.create_curity_task_definition(
            construct, curity_image, config, admin_service
        )

        #
        #  Create the Fargate Service
        #
        #  As we don't want a public load-balance we aren't using
        #  ApplicationLoadBalancedFargateService YET
        # ====================================================================
        self.curity_service = ecs.FargateService(
            construct,
            "CurityAdminService",
            task_definition=admin_task_definition,
            cluster=curity_cluster,
            enable_execute_command=True,   # If set, then CDK will also update the Task Role for us.
            service_name="curity-admin-service",
            cloud_map_options=ecs.CloudMapOptions(name="admin"),
            desired_count=1,
        )

        # TODO from here
        # load_balancer = lb.ApplicationLoadBalancer(
        #    construct, "LB", vpc=curity_cluster.vpc, internet_facing=False
        # )
