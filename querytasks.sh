#!/bin/sh
# find the instance ID based on Tag Name
#!/bin/bash

# Set the cluster name
CLUSTER_NAME=curity-cluster

# Get a list of task ARNs in the cluster
TASK_ARNS=$(aws ecs list-tasks --cluster ${CLUSTER_NAME} --query "taskArns[]" --output text --profile home)


# Loop through each task ARN and describe the task
for TASK_ARN in $TASK_ARNS
do
  # Use a query filter to get the ipAddress, lastStatus, and group attributes
  QUERY="tasks[].{IpAddress: containers[].networkInterfaces[].privateIpv4Address | [0], Status: lastStatus, Group: group}"

  # Describe the task using the query filter
  echo "Describing task ${TASK_ARN}"
  aws ecs describe-tasks --cluster ${CLUSTER_NAME} --tasks ${TASK_ARN} --query "${QUERY}" --profile home
  echo ""
done
