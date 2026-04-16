"""CDK stack: S3 bucket, SSL-only bucket policy, and an S3-triggered Lambda.

The assessment requires infrastructure that reacts when objects are created in S3.
This stack wires OBJECT_CREATED notifications to a Python handler that reads the
uploaded object and parses its first line (see ``lambda_src/processor.py``).
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications,
)
from constructs import Construct

class SixthStreet(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the S3 Bucket
        data_bucket = s3.Bucket(
            self, "DataProcessingBucket",
            versioned=True,
            # Destroy the bucket on stack deletion for easy cleanup
            removal_policy=RemovalPolicy.DESTROY, 
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # Create Explicit S3 Bucket Policy
        # Best practice: Deny non-SSL requests to the bucket
        bucket_policy = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            actions=["s3:*"],
            resources=[data_bucket.bucket_arn, data_bucket.arn_for_objects("*")],
            principals=[iam.AnyPrincipal()],
            conditions={
                "Bool": {"aws:SecureTransport": "false"}
            }
        )
        data_bucket.add_to_resource_policy(bucket_policy)

        # Create the Lambda Function
        processor_lambda = _lambda.Function(
            self, "FileProcessorLambda",
            runtime=_lambda.Runtime.PYTHON_3_14,
            handler="processor.handler",
            code=_lambda.Code.from_asset("lambda_src"),
            # Exposes bucket name for logging, tests, or future handler logic 
            # The runtime event also includes the bucket name for each invocation
            environment={
                "BUCKET_NAME": data_bucket.bucket_name
            }
        )

        # Grant Lambda read permissions to the bucket
        data_bucket.grant_read(processor_lambda)

        # Add S3 Event Notification to trigger Lambda on object creation
        notification = s3_notifications.LambdaDestination(processor_lambda)
        data_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, notification)