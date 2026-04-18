"""
Runs a live post-deployment integration check against the deployed Dev stack.
The test uploads a file to S3 and asserts Lambda processing by detecting the expected value in CloudWatch Logs.
"""
import time
import boto3
import pytest

def test_live_cloud_processing():
    """
    WARNING: This test interacts with the live AWS environment.
    It requires active AWS credentials and a deployed Dev stack.
    """
    cfn = boto3.client('cloudformation')
    s3 = boto3.client('s3')
    logs = boto3.client('logs')
    
    stack_name = "SixthStreetAssessment-Dev"
    
    # Fetch stack resources from CloudFormation
    try:
        response = cfn.list_stack_resources(StackName=stack_name)
    except Exception as e:
        pytest.fail(f"Could not find stack '{stack_name}'. Have you run 'cdk deploy SixthStreetAssessment-Dev'? Error: {e}")

    resources = response['StackResourceSummaries']
    
    # Dynamically extract BOTH the Bucket and the explicit Log Group
    try:
        bucket_name = next(r['PhysicalResourceId'] for r in resources if r['ResourceType'] == 'AWS::S3::Bucket')
        log_group_name = next(r['PhysicalResourceId'] for r in resources if r['ResourceType'] == 'AWS::Logs::LogGroup')
    except StopIteration:
        pytest.fail("Could not find the expected S3 Bucket or Log Group in the deployed stack.")
    
    test_file_key = f"integration-test-{int(time.time())}.txt"
    test_content = b"INTEGRATION_TEST_SUCCESS"

    # Upload a file to the live S3 bucket
    s3.put_object(Bucket=bucket_name, Key=test_file_key, Body=test_content)
    
    # Polling Mechanism for CloudWatch Logs
    max_retries = 5
    wait_seconds = 10
    logs_found = False
    
    print(f"\nWaiting for CloudWatch to ingest logs in {log_group_name}...")
    
    try:
        for attempt in range(max_retries):
            time.sleep(wait_seconds)
            
            log_events = logs.filter_log_events(
                logGroupName=log_group_name,
                filterPattern="INTEGRATION_TEST_SUCCESS"
            )
            
            if len(log_events.get('events', [])) > 0:
                logs_found = True
                print(f"Success! Logs found on attempt {attempt + 1}.")
                break
                
            print(f"Attempt {attempt + 1}/{max_retries}: Logs not yet ingested. Waiting...")
            
    finally:
        # Cleanup
        s3.delete_object(Bucket=bucket_name, Key=test_file_key)
        
    # Final Assertion
    assert logs_found, "Lambda failed to process the S3 file, or CloudWatch log ingestion timed out."