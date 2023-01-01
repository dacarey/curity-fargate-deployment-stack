#!/bin/sh
# find the instance ID based on Tag Name
INSTANCE_ID=$(aws ec2 describe-instances \
               --filter "Name=tag-value,Values=curity-bastion" \
               --query "Reservations[].Instances[?State.Name == 'running'].InstanceId[]" \
               --output text \
               --profile home)
# create an ssm session
aws ssm start-session --target $INSTANCE_ID --profile home
