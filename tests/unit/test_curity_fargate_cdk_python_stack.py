import aws_cdk as core
import aws_cdk.assertions as assertions

from curity_fargate_cdk_python.curity_fargate_cdk_python_stack import CurityFargateCdkPythonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in curity_fargate_cdk_python/curity_fargate_cdk_python_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CurityFargateCdkPythonStack(app, "curity-fargate-cdk-python")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
