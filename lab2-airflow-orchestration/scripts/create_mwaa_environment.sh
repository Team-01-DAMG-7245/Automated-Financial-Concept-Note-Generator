#!/usr/bin/env bash
set -euo pipefail

# ======= Prereqs =======
# aws configure (or AWS_PROFILE)
# jq installed (optional but recommended)
# You must have already staged:
#   s3://$MWAA_BUCKET/requirements.txt
#   s3://$MWAA_BUCKET/dags/...

# ======= Config (from your env) =======
: "${AWS_REGION:=us-east-1}"
: "${AWS_PROFILE:=default}"
: "${PROJECT_NAME:?set PROJECT_NAME}"
: "${MWAA_BUCKET:?set MWAA_BUCKET}"                   # e.g., aurelia-3c28b5-mwaa
: "${VPC_ID:?set VPC_ID}"
: "${SUBNET_1:?set SUBNET_1}"                         # private subnet
: "${SUBNET_2:?set SUBNET_2}"                         # private subnet
: "${SECURITY_GROUP:?set SECURITY_GROUP}"
: "${MWAA_EXECUTION_ROLE_ARN:?set MWAA_EXECUTION_ROLE_ARN}"

ENV_NAME="${PROJECT_NAME}-mwaa"                       # e.g., aurelia-mwaa
DAGS_S3_PATH="dags"                                   # we staged to bucket root /dags
REQ_S3_PATH="requirements.txt"                        # bucket root /requirements.txt
SOURCE_BUCKET_ARN="arn:aws:s3:::${MWAA_BUCKET}"

echo "Creating MWAA environment: ${ENV_NAME} in ${AWS_REGION}"
echo "Bucket: s3://${MWAA_BUCKET}  DAGs path: ${DAGS_S3_PATH}"

# ======= Create environment WITHOUT requirements first =======
aws mwaa create-environment \
  --region "${AWS_REGION}" \
  --name "${ENV_NAME}" \
  --airflow-version "2.7.2" \
  --environment-class "mw1.small" \
  --execution-role-arn "${MWAA_EXECUTION_ROLE_ARN}" \
  --source-bucket-arn "${SOURCE_BUCKET_ARN}" \
  --dag-s3-path "${DAGS_S3_PATH}" \
  --network-configuration "{
    \"SecurityGroupIds\": [\"${SECURITY_GROUP}\"],
    \"SubnetIds\": [\"${SUBNET_1}\", \"${SUBNET_2}\"]
  }" \
  --logging-configuration "{
    \"DagProcessingLogs\": {\"Enabled\": true, \"LogLevel\": \"INFO\"},
    \"SchedulerLogs\":     {\"Enabled\": true, \"LogLevel\": \"INFO\"},
    \"TaskLogs\":          {\"Enabled\": true, \"LogLevel\": \"INFO\"},
    \"WebserverLogs\":     {\"Enabled\": true, \"LogLevel\": \"INFO\"},
    \"WorkerLogs\":        {\"Enabled\": true, \"LogLevel\": \"INFO\"}
  }" \
  >/dev/null

echo "Environment creation submitted. Polling status..."

# ======= Wait until Available =======
while true; do
  STATUS=$(aws mwaa get-environment --name "${ENV_NAME}" --region "${AWS_REGION}" --query 'Environment.Status' --output text 2>/dev/null || echo "UNKNOWN")
  echo "Status: ${STATUS}"
  if [[ "${STATUS}" == "AVAILABLE" ]]; then
    break
  elif [[ "${STATUS}" == "CREATE_FAILED" || "${STATUS}" == "FAILED" ]]; then
    echo "ERROR: Environment failed to create."
    aws mwaa get-environment --name "${ENV_NAME}" --region "${AWS_REGION}" --output json
    exit 1
  fi
  sleep 30
done

# ======= Set requirements path and trigger install =======
echo "Setting requirements path to s3://${MWAA_BUCKET}/${REQ_S3_PATH}"
aws mwaa update-environment \
  --region "${AWS_REGION}" \
  --name "${ENV_NAME}" \
  --requirements-s3-path "${REQ_S3_PATH}" \
  >/dev/null

# Optional: you can also set env vars here via --imports if you prefer doing it in console later.
# Example:
# aws mwaa update-environment --name "${ENV_NAME}" \
#   --airflow-configuration-options '{
#     "[core]": {"load_examples": "False"}
#   }'

echo "Update submitted. Monitoring requirements installation..."

# ======= (Optional) Poll until requirements are applied =======
# MWAA doesn't expose a direct 'requirements status' flag, but you can
# wait a minute then open CloudWatch to confirm 'Successfully installed ...'.
sleep 60
echo "Open CloudWatch Logs for aws/airflow/${ENV_NAME} to confirm install success."
echo "Done. MWAA env '${ENV_NAME}' is ready to use."
