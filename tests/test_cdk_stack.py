import os
import sys
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

# Import infra / stack libraries
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'infra')))
from cdk_stack import SixthStreet

# Generate the template once for all tests to use
def get_template():
    app = cdk.App()
    stack = SixthStreet(app, "TestStack")
    return Template.from_stack(stack)

def test_s3_bucket_created_with_secure_defaults():
    template = get_template()

    # Assert we match our intended application bucket, not just any bucket.
    matches = template.find_resources("AWS::S3::Bucket", {
        "Properties": {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            },
            "VersioningConfiguration": {
                "Status": "Enabled"
            }
        }
    })
    assert len(matches) == 1
    logical_id = next(iter(matches))
    assert logical_id.startswith("DataProcessingBucket") # Match our bucket's name

def test_s3_bucket_policy_enforces_ssl():
    template = get_template()

    # Assert the bucket policy explicitly denies non-secure transport
    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "PolicyDocument": {
            "Statement": Match.array_with([
                Match.object_like({
                    "Action": "s3:*",
                    "Condition": {
                        "Bool": {"aws:SecureTransport": "false"}
                    },
                    "Effect": "Deny",
                    "Principal": {"AWS": "*"}
                })
            ])
        }
    })

def test_strict_compliance_enables_object_lock():
    # Instantiate the app WITH the context flag turned on
    app = cdk.App(context={"strict_compliance": "true"})
    stack = SixthStreet(app, "TestStack")
    template = Template.from_stack(stack)

    # Assert that the S3 Bucket now contains the WORM/Object Lock property
    template.has_resource_properties("AWS::S3::Bucket", {
        "ObjectLockEnabled": True
    })

def test_lambda_function_created():
    template = get_template()

    # Assert our file-processor Lambda exists 
    # Template also contains CDK-generated Lambda for bucket notifications and auto-delete.
    matches = template.find_resources("AWS::Lambda::Function", {
        "Properties": {
            "Handler": "processor.handler",
            "Runtime": "python3.14",
        }
    })
    assert len(matches) == 1

