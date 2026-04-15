#! /usr/bin/env python3
import aws_cdk as cdk
from infra.cdk_stack import SixthStreet

app = cdk.App()
SixthStreet(app,"SixthStreetAssessment")
app.synth()
