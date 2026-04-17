"""
This script sets up a lambda handler for S3 object-created events.

AWS invokes this with an event containing bucket and key; 
we fetch the object, take the first line of the file body, and log it.

The S3 notification (Object created) is set up at the end of our infra/cdk_stack.py code.
"""
import urllib.parse
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def handler(event, context):
    # Extract bucket name and object key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    logger.info(f"Triggered by file: {key} in bucket: {bucket}")
    
    try:
        # Fetch the file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        
        # Read and parse the single line file
        file_content = response['Body'].read().decode('utf-8')
        lines = file_content.splitlines()
        
        if lines:
            single_line = lines[0]
            logger.info(f"Successfully parsed single line content: {single_line}")
            return {
                "statusCode": 200,
                "body": f"Processed line: {single_line}"
            }
        else:
            logger.warning(f"File {key} is empty.")
            return {
                "statusCode": 204,
                "body": "File was empty"
            }
            
    except Exception as e:
        logger.error(f"Error getting object {key} from bucket {bucket}. Error: {str(e)}")
        raise e