from aws_cdk import (
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
    aws_iam as iam,
)


class BaseFargateService:

    #
    #  Choose the Docker Admin Image
    # =========================================================================
    @staticmethod
    def chooseDockerAdminImage(construct):
        curityAdminImage = ecr_assets.DockerImageAsset(
            construct,
            "CurityAdminImage",
            directory="../curity-docker-provisioning/clustered-env",
            file="Dockerfile.admin",
        )

        return curityAdminImage

    #
    #  Choose the Docker Runtime Image
    # =========================================================================
    @staticmethod
    def chooseDockerRuntimeImage(construct):
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
    @staticmethod
    def createCurityTaskDefinition(construct, curityImage, adminTask):
        # See https://curity.io/docs/idsvr/latest/system-admin-guide/system-requirements.html
        # for actual System Requirments.  e.g.  In production 8GB is recommended
        curity_admin_task_definition = ecs.FargateTaskDefinition(
            construct,
            "curity-admin-task" if adminTask else "curity-runtime-task",
            cpu=1024,
            memory_limit_mib=4096,
        )

        container_port_mappings = [
            ecs.PortMapping(container_port=8443, host_port=8443),
            ecs.PortMapping(container_port=6749, host_port=6749),
            ecs.PortMapping(container_port=4465, host_port=4465),
            ecs.PortMapping(container_port=4466, host_port=4466),
        ]

        if adminTask:
            container_port_mappings.append(
                ecs.PortMapping(container_port=6789, host_port=6789)
            )

        container_name = (
          "curity-admin-container" if adminTask else "curity-runtime-container"
        )
        curity_admin_task_definition.add_container(
            container_name,
            image=ecs.ContainerImage.from_docker_image_asset(curityImage),
            port_mappings=container_port_mappings,
            logging=ecs.AwsLogDriver(
                stream_prefix="curityadmin" if adminTask else "curityruntime",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
            ),
        )

        #
        # This list of permissions is curated from these sources
        # 1/ The first 7 permissions are essentially derived from
        #   https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
        #   1a/ N.B. Possibly I could optimise this first set to use the AWS
        #       recommended AmazonECSTaskExecutionRolePolicy.  See
        #       https://www.evernote.com/client/web?login=true#?b=533976b7-9966-468e-a6bd-c643b2eef72a&n=9241277e-3b27-48d1-addb-770bb444655c&
        # 2/ The additional set of ssmmessages permissions are derived from
        #    https://aws.amazon.com/blogs/containers/new-using-amazon-ecs-exec-access-your-containers-fargate-ec2/

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
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenControlChannel",
                    "ssmmessages:OpenDataChannel",
                ],
                resources=["*"],
            )
        )

        return curity_admin_task_definition
