#!/bin/bash

echo "Starting Step 2: Validating local CDK state against AWS environment..."

# Run cdk diff and capture the exit code. 
# The --fail flag ensures the command returns a non-zero exit code if differences exist.
cdk diff --fail

DIFF_EXIT_CODE=$?

if [ $DIFF_EXIT_CODE -eq 0 ]; then
  echo "✅ Success: No drift detected. Local code matches deployed infrastructure."
  exit 0
else
  echo "❌ Error: Infrastructure differences detected! Please review the diff above."
  echo "Run 'cdk deploy' to synchronize your environment."
  exit 1
fi