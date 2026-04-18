"""
Implements the Lambda handler invoked by S3 object-created notifications.
The handler reads the uploaded object, logs processing details, and returns the first parsed line when content exists.
"""
import urllib.parse
import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize Powertools Logger
logger = Logger(service="FileProcessorService")

s3 = boto3.client('s3')

# Inject context into the logger for automatic tracing
@logger.inject_lambda_context(log_event=True)
def handler(event: dict, context: LambdaContext):
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    # Powertools will output this as a clean JSON object with Request IDs attached
    logger.info("Processing S3 Event", extra={"bucket_name": bucket, "file_key": key})
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        lines = file_content.splitlines()
        
        if lines:
            single_line = lines[0]
            logger.info("Successfully parsed file", extra={"parsed_content": single_line})
            return {"statusCode": 200, "body": f"Processed line: {single_line}"}
        else:
            logger.warning("File was empty")
            return {"statusCode": 204, "body": "File was empty"}
            
    except Exception as e:
        # Powertools automatically captures and formats the stack trace
        logger.exception("Failed to process S3 object")
        raise e