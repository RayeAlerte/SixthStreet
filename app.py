#! /usr/bin/env python3
"""
AWS CDK App "Main" Function/Entrypoint:
This script instantiates the ``SixthStreet`` Dev + Production S3 stack. (see ``infra/cdk_stack.py``)

It reads account and region from standard CDK environment variables, applies
branch-aligned compliance defaults per stack (Dev relaxed, Prod strict), and
then synthesizes both stacks into deployable CloudFormation templates.
"""
import os
import aws_cdk as cdk
from infra.cdk_stack import SixthStreet

app = cdk.App()

# Shared environment configuration pulling from terminal/pipeline
aws_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"), 
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# Development Environment (Clean testing pipeline target)
SixthStreet(
    app, 
    "SixthStreetAssessment-Dev", 
    env=aws_env,
    is_strict_compliance=False
)

# Production Environment (Live workload)
SixthStreet(
    app, 
    "SixthStreetAssessment-Prod", 
    env=aws_env,
    is_strict_compliance=True
)

app.synth()