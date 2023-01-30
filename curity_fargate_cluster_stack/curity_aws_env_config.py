"""This module support retrieving and validatind configuration data from the cdk.json file."""
from jsonschema import validate
from aws_cdk import App

schema = {
    "type": "object",
    "properties": {
        "vpcname": {"type": "string"},
    },
    "required": ["vpcname"],
}


def get_config(app:App):
    """get the target identifier"""
    target = app.node.try_get_context(key="target")
    if not target:
        raise LookupError(
            "The 'target' variable missing on the cdk command."
            + "See cdk.json for available values, e.g. 'dw-dev','dw-sit', 'dw-uat'."
            + "Then pass these into you cdk command as '-c target=dw-dev"
        )

    print(f"target value is {target}")

    target_config = app.node.try_get_context(key=target)
    if not target_config:
        raise LookupError(
            f"The '{target}' target node is not configured in the cdk.json file"
        )

    validate(instance=target_config, schema=schema)

    return target_config
