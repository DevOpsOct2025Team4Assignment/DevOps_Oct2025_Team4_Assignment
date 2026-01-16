#!/bin/bash

echo "Starting QA Automated Checks..."
sleep 2

# Simulate a failure
echo "Error: Critical vulnerability found in dependency 'example-lib'"
echo "Error: QA check failed at $(date)"

# Returning any number other than 0 tells GitHub the job failed
exit 1