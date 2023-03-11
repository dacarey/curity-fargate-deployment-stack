"""This module provides the CurityRuntimeService class."""
from aws_cdk import (
    aws_ecs_patterns as ecspattern,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as lb,
    aws_route53 as route53,
    aws_ec2 as ec2,
)
from curity_fargate_cluster_stack.base_fargate_service import (
    BaseFargateService
)


class CurityRuntimeService(BaseFargateService):
    """This class constricts a Fargate Service to represent a set of Curity Runtime nodes."""

    def __init__(self, construct, curity_cluster, config):
        #
        # Prepare the Container and associated ECS Task
        # ====================================================================
        curity_image = CurityRuntimeService.choose_docker_runtime_image(construct)

        runtime_task_definition = self.create_curity_task_definition(
            construct, curity_image, config,  False
        )

        #
        #  The Load Balancer needs a public dns zone
        # ====================================================================
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            construct,
            "HostedZone",
            zone_name="aws.redkitehill.com",
            hosted_zone_id="Z06756123LAL436U5E34J",
        )

        #
        #  Create the Load Balancer and the BackEnd Service
        #  Additional notes compared to the simple doc examples
        #  - This auto-handles creating a certificate for use with https
        #  - It auto handles DNS registration with the supplied 'domain-name'
        #  - We configure service discovery ( via cloud map) for the
        #    container tasks in the backend.
        #  - We enable the SSM execute-command option to allow debugging
        #    into the containers
        # ====================================================================
        self.curity_service = ecspattern.ApplicationLoadBalancedFargateService(
            construct,
            "CurityRuntimeService",
            listener_port=443,
            protocol=lb.ApplicationProtocol.HTTPS,
            domain_zone=hosted_zone,
            task_definition=runtime_task_definition,
            domain_name="curity.aws.redkitehill.com",
            target_protocol=lb.ApplicationProtocol.HTTPS,
            load_balancer_name="curity-lb",
            cluster=curity_cluster,
            enable_execute_command=True,   # If set, then CDK will also update the Task Role for us.
            service_name="curity-runtime-service",
            cloud_map_options=ecs.CloudMapOptions(name="runtime"),
        )

        #
        # Setup the HealthCheck ping from the LB
        self.curity_service.target_group.configure_health_check(
            port="4465",
            protocol=lb.Protocol.HTTP,
            # timeout=Duration.seconds(20),
            # interval=Duration.seconds(30),
            # unhealthy_threshold_count=10
        )

        # https://github.com/aws/aws-cdk/issues/18093
        # We have to additionally allow the LB Service to
        # accept the Healthcheck WHERE it is on a different port
        self.curity_service.service.connections.allow_from(
            self.curity_service.load_balancer,
            ec2.Port.tcp(4465),
            "Allow access from LB to the Fargate Service Healthcheck Port",
        )
