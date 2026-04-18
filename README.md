# Sixth Street Assessment: Cloud Infrastructure Engineer

## Architecture Overview
![Architecture Diagram](./architecture.png)

This repository contains an AWS CDK application written in Python that provisions an S3 Bucket and a serverless Lambda function. When a file is dropped into the S3 bucket, an event notification triggers the Lambda function, which fetches the file and parses its single-line contents.

## Key Features & Security Posture
* **Infrastructure as Code:** Fully modeled in AWS CDK (Python).
* **Least Privilege:** The Lambda function only possesses read permissions for the specific S3 bucket it is subscribed to.
* **Bucket Policies:** Explicit bucket policies block all public access and enforce secure transport (SSL/TLS) for all operations.
* **Automated Cleanup:** The S3 bucket is configured with `RemovalPolicy.DESTROY` and `auto_delete_objects=True` to ensure the environment is cleanly spun down without orphaned resources.

## Prerequisites
* Python 3.14+
* An AWS account with appropriate CLI permissions, an access key ID, and secret key
* AWS CLI installed and configured (`aws configure`)
    - Download the latest version from https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html.
    - Provide Access Key ID, Secret Key, Default Region (example: us-east-2), Default Output Format (example: json)
* AWS CDK CLI installed 
    - Node JS Install (`npm install -g aws-cdk`)
    - Homebrew (MacOS) (`brew install aws-cdk`)

* Requirements (Production):
    - Requirements.txt contains all prerequisite libraries to launch this AWS stack.
    - This includes: 
        aws-cdk-lib,
        boto3, 
        aws/constructs.

* Requirements (Development):
    - Requirements-dev.txt contains additional libraries used to perform tests against our AWS stack.
    - This includes:
        moto[s3] - Library to generate mock AWS services (S3)
        pytest - Library to create Python tests

## Local Development & Testing Pipeline

This project utilizes a three-step testing pipeline to validate application logic, infrastructure configuration, and cloud state before deployment.

1. **Clone the repository and set up a virtual environment:**

        python3 -m venv .venv
        source .venv/bin/activate

2. **Install deployment and development dependencies:**

        pip install -r requirements.txt
        pip install -r requirements-dev.txt

3. **Bootstrap the CDK environment:**
        
        Deploy the bootstrap stack to your environment (required for deploying future assets).
            cdk bootstrap

4. **Run the Testing Pipeline:**
   * **Step 0 & 1 (Local Unit Tests):** Validates the Lambda parsing logic using `moto` to mock S3, and utilizes the CDK Assertions library to verify the generated CloudFormation template enforces strict security policies.

            pytest tests/

   * **Step 2 (Cloud State Validation):** Compares the local CDK code against the current state of your AWS environment to detect drift and preview IAM changes before deployment.

            chmod +x tests/validate_state_diff.sh
            ./tests/validate_state_diff.sh

## Deploy to Production

1. **Bootstrap the environment (Required once per AWS account/region):**

        cdk bootstrap

2. **Deploy the stack:**

        cdk deploy

## CI/CD Deployment Workflow
Included in `.github/workflows/deploy.yml` is a GitHub Actions workflow. When code is pushed to the `main` branch, the workflow automatically:
1. Sets up the Python and Node.js environments.
2. Installs AWS CDK and Python dependencies.
3. Authenticates with AWS using repository secrets (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`).
4. Executes `cdk deploy --require-approval never` to deploy the infrastructure.

## Maintenance and Teardown
To test the S3 bucket trigger and lambda function manually:
1. Navigate to the AWS Console -> S3.
2. Upload a `.txt` file containing a single line of text to the newly created bucket.
3. Navigate to CloudWatch -> Log Groups -> `/aws/lambda/<YourLambdaFunctionName>`.
4. Verify the parsed single line is successfully printed in the logs.

**To destroy all resources and prevent billing, run:**

        cdk destroy