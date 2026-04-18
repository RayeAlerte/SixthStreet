"""
Defines the SixthStreet CDK stack for both environments, including a hardened S3 bucket, a Python Lambda processor, and S3-to-Lambda event wiring.
The stack toggles retention and compliance controls via the strict_compliance context while preserving secure defaults.
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    Aws,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_s3_notifications as s3_notifications,
)
from constructs import Construct

class SixthStreet(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Check for CDK context flag to select for removal, retention, autodelete
        is_strict_compliance = self.node.try_get_context("strict_compliance") == "true"
        compliance_removal_policy = RemovalPolicy.RETAIN if is_strict_compliance else RemovalPolicy.DESTROY
        compliance_auto_delete = False if is_strict_compliance else True
        compliance_log_retention = logs.RetentionDays.INFINITE if is_strict_compliance else logs.RetentionDays.ONE_MONTH

        # Define your baseline properties for ALL buckets
        bucket_props = {
            "versioned": True,
            "removal_policy": compliance_removal_policy,
            "auto_delete_objects": compliance_auto_delete,
            "block_public_access": s3.BlockPublicAccess.BLOCK_ALL,
        }

        # Define properties for high-compliance buckets only
        if is_strict_compliance:
            compliance_props = {
                "object_lock_enabled": True, # WORM storage
                "encryption": s3.BucketEncryption.KMS_MANAGED, # Auditable encryption
            }
            # Merge compliance props into the baseline using Python dict unpacking
            bucket_props = {**bucket_props, **compliance_props}

        # Instantiate the bucket using the property dictionary
        data_bucket = s3.Bucket(
            self, 
            "DataProcessingBucket",
            **bucket_props
        )

        # Apply explicit SSL required bucket policy
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
        
        # Fetch the official AWS Powertools V3 Layer for Python 3.14 / JSON Logging in Lambda
        powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, id="PowertoolsLayer",
            layer_version_arn=f"arn:aws:lambda:{Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python314-x86_64:27"
        )

        # Define the Log Group
        processor_log_group = logs.LogGroup(
            self, "ProcessorLogGroup",
            retention=compliance_log_retention, # Base retention on strict_compliance flag
            removal_policy=compliance_removal_policy # Ensures 'cdk destroy' deletes the logs in Dev (Not Prod)
        )

        # Create the Lambda Function with logging, dependencies, code
        processor_lambda = _lambda.Function(
            self, "FileProcessorLambda",
            runtime=_lambda.Runtime.PYTHON_3_14,
            handler="processor.handler",
            code=_lambda.Code.from_asset("lambda_src"),
            timeout=Duration.seconds(10), # Helps cold start issues
            log_group=processor_log_group, # Name of the lambda log group
            layers=[powertools_layer], # Binds Powertools library
            environment={
                "BUCKET_NAME": data_bucket.bucket_name
            }
        )

        # Grant Lambda read permissions to the bucket
        data_bucket.grant_read(processor_lambda)

        # Add S3 Event Notification to trigger Lambda on object creation
        notification = s3_notifications.LambdaDestination(processor_lambda)
        data_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, notification)