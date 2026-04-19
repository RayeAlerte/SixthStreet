# Sixth Street Assessment: Cloud Infrastructure Engineer

## Architecture Overview
![Architecture Diagram](./architecture.png)

This repository contains an AWS CDK application written in Python that provisions an S3 Bucket and a serverless Lambda function. When a file is dropped into the S3 bucket, an event notification triggers the Lambda function, which fetches the file and parses its single-line contents.

## Key Features & Security Posture
* **Infrastructure as Code:** Fully modeled in AWS CDK (Python).
* **Least Privilege:** The Lambda function only possesses read permissions for the specific S3 bucket it is subscribed to.
* **Universal S3 Bucket Policies:** Explicit bucket policies block all public access and enforce secure transport (SSL/TLS) for all operations.
* **Dev + Prod Deployment Targets:** Two environments: SixthStreetAssessment-Dev (relaxed compliance) and SixthStreetAssessment-Prod (strict compliance).
    - Strict Compliance Policies (Production):
        - Enable Customer Managed Keys (SSE-KMS Encryption) for Auditing
        - Retain Buckets and Log Groups after stack deletion
        - Keep CloudWatch logs indefinitely
    - Relaxed Compliance Policies (Development):
        - Delete Buckets and Log Groups after stack deletion (`RemovalPolicy.DESTROY` and `auto_delete_objects=True`)
        - Keep CloudWatch logs for 30 days
* **Structured Logging**: Uses Lambda Powertools to support JSON formatted logging to "ProcessorLogGroup".
* **Automated Cleanup:** Dev environment S3 bucket is configured to ensure the environments are cleanly spun down without orphaned resources.

## Prerequisites
* Python 3.14+
* An AWS account with appropriate CLI permissions, an access key ID, and secret key
* AWS CLI installed and configured
    - Download the latest version from https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html.
    - Run configuration (`aws configure`)
        - Provide Access Key ID, Secret Key, Default Region (example: us-east-2), Default Output Format (example: json)
* AWS CDK CLI installed - either as:
    - NodeJS NPM Package (`npm install -g aws-cdk`)
    - Homebrew (macOS, includes NodeJS) (`brew install aws-cdk`)
    - After installing, bootstrap the environment using:
        cdk bootstrap
* Requirements (Production):
    - Requirements.txt contains all prerequisite libraries to launch this AWS stack.
    - This includes: 
        aws-cdk-lib,
        boto3,
        aws/constructs,
        aws-lambda-powertools.
* Requirements (Development):
    - Requirements-dev.txt contains additional libraries used to perform tests against our AWS stack.
    - This includes:
        moto[s3],
        pytest.

## Preview Stack and Run Tests Locally

This project utilizes a three-step testing pipeline to validate application logic, infrastructure configuration, and cloud state before deployment.

1. **Clone the repository and set up a virtual environment:**

        python3 -m venv .venv
        # Unix: source .venv/bin/activate      
        # Windows: .venv\Scripts\activate

2. **Install dependencies:**

        pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

3. **Run the Testing Pipeline:**
   * **Step 0 & 1 (Local Unit Tests):** Validates the Lambda parsing logic using `moto` to mock S3, and utilizes the CDK Assertions library to verify the generated CloudFormation template enforces strict security policies.

            pytest tests/

   * **Step 2 (Cloud State Validation):** Compares the local CDK code against the current state of your AWS environment to detect drift and preview IAM changes before deployment.

            chmod +x tests/validate_state_diff.sh
            ./tests/validate_state_diff.sh

## CI/CD Deployment Workflow

Automated deployments are handled via a GitHub Actions workflow defined in `.github/workflows/deploy.yml`. This pipeline enforces testing, routes deployments based on the active branch, and prevents incidental redeployment.

### Pipeline Process
When code is pushed to the `main` or `dev` branches (or a Pull Request is opened), the workflow executes the following sequence:

1. Skip execution if a commit exclusively modifies documentation (e.g., `README.md`, `.gitignore`, or architecture diagrams).
2. Set up the Python and Node.js environments, install dependencies, and execute the local `pytest` suite (`test_processor.py` and `test_cdk_stack.py`). **Deployments are strictly blocked if these tests fail.**
3. If tests pass on `push`, the workflow authenticates with AWS using repository secrets and dynamically targets a stack:
   - Pushes to `main` deploy to the strict compliance `SixthStreetAssessment-Prod` stack.
   - Pushes to `dev` deploy to the relaxed compliance `SixthStreetAssessment-Dev` stack.
4. **Post-Deployment Validation:** If the deployment targeted the `dev` branch, the pipeline runs a live integration test (`validate_post_deployment.py`) against the newly deployed cloud resources to ensure end-to-end functionality.

### Deployment Strategy (Dev to Prod)
This repository follows a multi-environment promotion strategy:

1. **Development (`dev` branch):** All new features, infrastructure changes, and standard bug fixes must be committed to the `dev` branch. Pushing to `dev` automatically updates the isolated Sandbox stack in AWS for testing.
2. **Production Promotion (`main` branch):** Direct pushes to `main` should be restricted. To deploy to Production, open a **Pull Request** from `dev` to `main`. Once the automated tests pass and the PR is merged, the pipeline provisions the highly compliant `SixthStreetAssessment-Prod` stack.
3. **Emergency Hotfixes:** For critical production bugs, create a temporary branch (e.g., `hotfix/issue-name`) directly off `main`. Open a PR against `main` for an immediate, tested deployment. Once deployed, merge `main` back into `dev` to keep environments synchronized.

### GitHub Repository Setup

To fully enable the automated pipeline and secure your infrastructure, you must configure the following settings directly in the GitHub UI:

**Configure AWS Secrets**
The pipeline requires scoped AWS credentials to provision infrastructure. 
1. Navigate to the repository's **Settings > Secrets and variables > Actions**.
2. Click **New repository secret** and add 2 items:
   * `AWS_ACCESS_KEY_ID`: Your IAM user/role access key.
   * `AWS_SECRET_ACCESS_KEY`: Your IAM user/role secret key.

**Enable Branch Protection**
To prevent accidental, untested deployments to Production, enforce branch protection on your `main` branch:
1. Navigate to **Settings > Branches** and click **Add branch protection rule**.
2. Set the **Branch name pattern** to `main`.
3. Check **Require a pull request before merging** (this prevents direct terminal pushes).
4. Check **Require status checks to pass before merging** and configure it to require the `pre_deploy_tests` job to succeed before the merge button becomes active.
5. Click **Create** to lock down the environment.

## Manual Deployment (Not Recommended)

If you need to deploy manually from your terminal (not recommended), execute the CDK commands using the explicit stack name after completing tests:

**Deploy the stack:**

        # Development (Relaxed Compliance)
        cdk deploy SixthStreetAssessment-Dev

        # Production (Strict Compliance)
        cdk deploy SixthStreetAssessment-Prod

**Perform a post-deployment test to verify functionality:**

        pytest tests/validate_post_deployment.py -s

## Maintenance and Teardown
To test the S3 bucket trigger and lambda function manually:
1. Navigate to the AWS Console -> S3.
2. Upload a `.txt` file containing a single line of text to the newly created bucket.
3. Navigate to CloudWatch -> Log Groups -> `/aws/lambda/<YourLambdaFunctionName>`.
4. Verify the parsed single line is successfully printed in the logs.

**To destroy all resources and prevent billing, run:**

        cdk destroy SixthStreetAssessment-Dev
        cdk destroy SixthStreetAssessment-Prod  # Retention policy prevents full deletion

**Expected future maintenance:**

Periodically update PYTHON_VERSION in GitHub Actions, Lambda runtime and Powertools Layer ARN in cdk_stack.py, and package versions (aws-cdk-lib) in requirements.txt and requirements-dev.txt.