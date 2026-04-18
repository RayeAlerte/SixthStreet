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
    
    # 1. Find the live S3 Bucket and Lambda physical IDs
    try:
        response = cfn.list_stack_resources(StackName=stack_name)
    except Exception as e:
        pytest.fail(f"Could not find stack '{stack_name}'. Have you run 'cdk deploy SixthStreetAssessment-Dev'? Error: {e}")

    resources = response['StackResourceSummaries']
    
    try:
        bucket_name = next(r['PhysicalResourceId'] for r in resources if r['ResourceType'] == 'AWS::S3::Bucket')
        lambda_name = next(r['PhysicalResourceId'] for r in resources if r['ResourceType'] == 'AWS::Lambda::Function' and 'FileProcessor' in r['LogicalResourceId'])
    except StopIteration:
        pytest.fail("Could not find the expected S3 Bucket or Lambda Function in the deployed stack.")
    
    log_group_name = f"/aws/lambda/{lambda_name}"
    test_file_key = f"integration-test-{int(time.time())}.txt"
    test_content = b"INTEGRATION_TEST_SUCCESS"

    # 2. Upload a file to the live S3 bucket
    s3.put_object(Bucket=bucket_name, Key=test_file_key, Body=test_content)
    
    # 3. Polling Mechanism for CloudWatch Logs
    max_retries = 6
    wait_seconds = 10
    logs_found = False
    
    print(f"\nWaiting for CloudWatch to ingest logs in {log_group_name}...")
    
    try:
        for attempt in range(max_retries):
            time.sleep(wait_seconds)
            
            # Since we upgraded to Powertools (JSON logs), the text will still be found
            # inside the raw JSON string payload in CloudWatch.
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
        # 4. Cleanup: Always delete the test file, even if the assertion fails
        s3.delete_object(Bucket=bucket_name, Key=test_file_key)
        
    # 5. Final Assertion
    assert logs_found, "Lambda failed to process the S3 file, or CloudWatch log ingestion timed out after 60 seconds."