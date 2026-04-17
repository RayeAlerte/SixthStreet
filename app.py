#! /usr/bin/env python3
"""
AWS CDK App "Main" Function/Entrypoint:

This script:
- instantiates the ``SixthStreet`` stack 
(see ``infra/cdk_stack.py``)
- ends with .synth() to convert to CloudFormation templates
"""
import os
import aws_cdk as cdk
from infra.cdk_stack import SixthStreet

app = cdk.App()
SixthStreet(app,"SixthStreetAssessment", 
            env=cdk.Environment(
            account=os.environ.get("CDK_DEFAULT_ACCOUNT"), 
            region=os.environ.get("CDK_DEFAULT_REGION")
        )
    )
app.synth()
