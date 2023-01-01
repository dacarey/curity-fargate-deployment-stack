from aws_cdk import (
    aws_ecs_patterns as ecspattern,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as lb,
    aws_route53 as route53,
    aws_ec2 as ec2,
    aws_iam as iam,
)


class CurityFargateService:
    def __init__(self, construct, curity_cluster, admin):
        curityImage = self.chooseDockerImage(construct, admin)

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            construct,
            "HostedZone",
            zone_name="aws.redkitehill.com",
            hosted_zone_id="Z06756123LAL436U5E34J",
        )

        curity_admin_task_definition = self.createCurityAdminTask(
            construct, curityImage
        )

        self.curity_service = ecspattern.ApplicationLoadBalancedFargateService(
            construct,
            "CurityService",
            listener_port=443,
            protocol=lb.ApplicationProtocol.HTTPS,
            domain_zone=hosted_zone,
            task_definition=curity_admin_task_definition,
            domain_name="curity.aws.redkitehill.com",
            target_protocol=lb.ApplicationProtocol.HTTPS,
            load_balancer_name="curity-lb",
            cluster=curity_cluster,
            enable_execute_command=True,
            service_name="curity-admin-service"
        )

        self.curity_service.target_group.configure_health_check(
            port="4465", protocol=lb.Protocol.HTTP
        )

        # https://github.com/aws/aws-cdk/issues/18093
        # We have to additionally allow the LB Service to
        # accept the Healthcheck WHERE it is on a different port
        self.curity_service.service.connections.allow_from(
            self.curity_service.load_balancer,
            ec2.Port.tcp(4465),
            "Allow access from LB to the Fargate Service Healthcheck Port",
        )

    #
    #  Choose a Docker Image based on whether we are acting
    #  as an admin node or a runtime node
    # =========================================================================
    def chooseDockerImage(self, construct, admin):
        if admin:
            curityAdminImage = ecr_assets.DockerImageAsset(
                construct,
                "CurityAdminImage",
                directory="../curity-docker-provisioning/clustered-env",
                file="Dockerfile.admin",
            )

            return curityAdminImage

        curityRuntimeImage = ecr_assets.DockerImageAsset(
            construct,
            "CurityRuntimeImage",
            directory="../curity-docker-provisioning/clustered-env",
            file="Dockerfile.runtime",
        )

        return curityRuntimeImage

    #
    #   create a Fargate Task Definition for the Curity Admin Docker image
    #
    #   Noteworthy:-
    #   1/ We are using the FargateTaskDefinition option with
    #      ApplicationLoadBalancedFargateService rather than the
    #      TaskImageOptions options because it allows more control
    #      over the Port Mappings
    #   2/ We are adding to the Task Definition to allow the use of
    #      the "aws ecs execute-command"  per these articles:-
    #      https://aws.amazon.com/blogs/containers/new-using-amazon-ecs-exec-access-your-containers-fargate-ec2/
    #      https://towardsthecloud.com/amazon-ecs-execute-command-access-container
    # =========================================================================
    def createCurityAdminTask(self, construct, curityImage):
        curity_admin_task_definition = ecs.FargateTaskDefinition(
            construct,
            "CurityAdminTaskDefinition",
            cpu=512,
            memory_limit_mib=2048,
        )

        curity_admin_task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:DescribeLogGroups",
                    "ssm:GetParameters",
                    "aps:RemoteWrite",
                ],
                resources=["*"],
            )
        )

        container_port_mappings = [
            ecs.PortMapping(container_port=8443, host_port=8443),
            ecs.PortMapping(container_port=6749, host_port=6749),
            ecs.PortMapping(container_port=4465, host_port=4465),
            ecs.PortMapping(container_port=4466, host_port=4466),
        ]

        self.container = curity_admin_task_definition.add_container(
            "CurityAdminContainer",
            image=ecs.ContainerImage.from_docker_image_asset(curityImage),
            port_mappings=container_port_mappings,
            logging=ecs.AwsLogDriver(
                stream_prefix="curityadmin",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING
            ),
        )

        curity_admin_task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenControlChannel",
                    "ssmmessages:OpenDataChannel",
                ],
                resources=["*"],
            )
        )

        return curity_admin_task_definition
