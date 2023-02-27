"""This module support retrieving and validatind configuration data from the cdk.json file."""
import os.path

from jsonschema import validate
from aws_cdk import App

schema = {
    "type": "object",
    "properties": {
        "vpcname": {"type": "string"},
        "envfile": {"type": "string"},
    },
    "required": ["vpcname"],
}


def get_config(app:App):
    """get the target identifier"""
    target = app.node.try_get_context(key="curity-aws-env")
    if not target:
        raise LookupError(
            "The 'curity-aws-env' variable missing on the cdk command."
            + "See cdk.json for available values, e.g. 'dw-dev','dw-sit', 'dw-uat'."
            + "Then pass these into you cdk command as '--context curity-aws-env=dw-dev"
        )

    target_config = app.node.try_get_context(key=target)
    if not target_config:
        raise LookupError(
            f"The '{target}' target node is not configured in the cdk.json file"
        )

    validate(instance=target_config, schema=schema)

    # Validate Optional Parameters if supplied

    # check if environment_file_path exists and add it to the container definition if it does
    environment_file_path = target_config.get("envfile")
    if environment_file_path and not os.path.isfile(environment_file_path):
        raise LookupError(
            f"The 'envfile' attribute is set to '{environment_file_path}'" +
            " in cdk.json but this file does not exist."
        )


    return target_config
