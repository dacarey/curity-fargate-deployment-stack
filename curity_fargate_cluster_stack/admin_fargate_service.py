from aws_cdk import (
    aws_ecs as ecs,
)
from curity_fargate_cluster_stack.base_fargate_service import (
    BaseFargateService
)


class CurityAdminService(BaseFargateService):
    def __init__(self, construct, curity_cluster, adminService):
        #
        # Prepare the Container and associated ECS Task
        # ====================================================================
        curityImage = CurityAdminService.chooseDockerAdminImage(construct)

        admin_task_definition = self.createCurityTaskDefinition(
            construct, curityImage, adminService
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
            enable_execute_command=True,
            service_name="curity-admin-service",
            cloud_map_options=ecs.CloudMapOptions(name="admin"),
            desired_count=1,
        )

        # TODO from here
        # load_balancer = lb.ApplicationLoadBalancer(
        #    construct, "LB", vpc=curity_cluster.vpc, internet_facing=False
        # )
