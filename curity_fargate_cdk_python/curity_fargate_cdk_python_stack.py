from aws_cdk import (
    Stack,
    aws_ecs_patterns as ecspattern,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct
from os import path


class CurityFargateCdkPythonStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        curityAdminImage = ecr_assets.DockerImageAsset(
            self,
            "CurityAdminImage",
            directory="../curity-docker-provisioning/clustered-env",
            file="Dockerfile.admin",
        )

        self.curity_service = ecspattern.ApplicationLoadBalancedFargateService(
            self,
            "CurityService",
            cpu=512,
            memory_limit_mib=2048,
            listener_port=443,
            task_image_options=ecspattern.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(curityAdminImage),
                container_port=8443,
            ),
        )
