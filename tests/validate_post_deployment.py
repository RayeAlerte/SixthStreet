import time
import boto3
import pytest

@pytest.mark.integration
def test_live_cloud_processing():
    """
    WARNING: This test interacts with your live AWS environment.
    It requires active AWS credentials and a deployed Dev stack.
    """
    cfn = boto3.client('cloudformation')
    s3 = boto3.client('s3')
    logs = boto3.client('logs')
    
    stack_name = "SixthStreetAssessment-Dev"
    
    # Find the live S3 Bucket and Lambda physical IDs from CloudFormation
    response = cfn.list_stack_resources(StackName=stack_name)
    resources = response['StackResourceSummaries']
    
    bucket_name = next(r['PhysicalResourceId'] for r in resources if r['ResourceType'] == 'AWS::S3::Bucket')
    lambda_name = next(r['PhysicalResourceId'] for r in resources if r['ResourceType'] == 'AWS::Lambda::Function' and 'FileProcessor' in r['LogicalResourceId'])
    
    log_group_name = f"/aws/lambda/{lambda_name}"
    test_file_key = f"integration-test-{int(time.time())}.txt"
    test_content = b"INTEGRATION_TEST_SUCCESS"

    # Upload a file to the live S3 bucket
    s3.put_object(Bucket=bucket_name, Key=test_file_key, Body=test_content)
    
    # Wait for S3 to trigger Lambda and CloudWatch to ingest logs
    time.sleep(10)
    
    # Query the live CloudWatch logs to verify processing
    log_events = logs.filter_log_events(
        logGroupName=log_group_name,
        filterPattern="INTEGRATION_TEST_SUCCESS"
    )
    
    # Assert that the Lambda successfully printed the string we uploaded
    assert len(log_events['events']) > 0, "Lambda failed to process the S3 file or logs did not appear."
    
    # Clean up the test file
    s3.delete_object(Bucket=bucket_name, Key=test_file_key)