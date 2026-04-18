"""
Tests Lambda processing behavior against mocked AWS services using moto.
The suite verifies the handler reads S3 content and returns only the expected parsed first line.
"""
import os
import sys
import json
import pytest
import boto3
from moto import mock_aws

# Set up to import lambda_src/processor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lambda_src')))

# Create a Mock Context for Lambda Powertools
class MockContext:
    def __init__(self):
        self.aws_request_id = "test-request-id-12345"
        self.function_name = "test-processor-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-processor-function"

# Setup Mock AWS Environment
@pytest.fixture
def aws_credentials():
    #Mock AWS Credentials for moto
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def s3_setup(aws_credentials):
    # Create a mock S3 client with our bucket and test file
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-data-bucket"
        file_key = "test-file.txt"
        
        # Create the mock bucket
        s3.create_bucket(Bucket=bucket_name)
        # Upload a mock file
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=b"This is the first line.\nThis is the second line.")
        
        yield {"bucket": bucket_name, "key": file_key}

# Test the Handler
def test_lambda_handler(s3_setup):
    # Import the lambda function AFTER moto is engaged
    import processor
    
    # Construct a mock S3 event payload that AWS would normally send
    mock_event = {
        "Records": [{
            "s3": {
                "bucket": {"name": s3_setup["bucket"]},
                "object": {"key": s3_setup["key"]}
            }
        }]
    }

    # Execute the handler
    context = MockContext()
    response = processor.handler(mock_event, context)

    # Assertions - Validate output
    assert response["statusCode"] == 200
    assert "This is the first line." in response["body"]
    assert "This is the second line." not in response["body"]