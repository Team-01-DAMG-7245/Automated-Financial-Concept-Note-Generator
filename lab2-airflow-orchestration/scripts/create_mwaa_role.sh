#!/bin/bash

set -e

export AWS_PROFILE=aurelia
export AWS_REGION=us-east-1

# Load environment
source .env

echo "🔐 Creating MWAA Execution Role..."
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Account ID: $ACCOUNT_ID"
echo "MWAA Bucket: $MWAA_BUCKET"
echo ""

# Create trust policy
mkdir -p /tmp/aurelia
cat > /tmp/aurelia/mwaa-trust-policy.json << TRUSTEOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "airflow-env.amazonaws.com",
          "airflow.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
TRUSTEOF

# Create execution policy
cat > /tmp/aurelia/mwaa-execution-policy.json << POLICYEOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "airflow:PublishMetrics",
      "Resource": "arn:aws:airflow:${AWS_REGION}:${ACCOUNT_ID}:environment/aurelia-mwaa"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject*",
        "s3:GetBucket*",
        "s3:List*"
      ],
      "Resource": [
        "arn:aws:s3:::${MWAA_BUCKET}",
        "arn:aws:s3:::${MWAA_BUCKET}/*",
        "arn:aws:s3:::aurelia-*",
        "arn:aws:s3:::aurelia-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject*"
      ],
      "Resource": [
        "arn:aws:s3:::aurelia-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents",
        "logs:GetLogEvents",
        "logs:GetLogRecord",
        "logs:GetLogGroupFields",
        "logs:GetQueryResults"
      ],
      "Resource": [
        "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:airflow-aurelia-mwaa-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "cloudwatch:PutMetricData",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ChangeMessageVisibility",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:ReceiveMessage",
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:${AWS_REGION}:*:airflow-celery-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey*",
        "kms:Encrypt"
      ],
      "NotResource": "arn:aws:kms:*:${ACCOUNT_ID}:key/*",
      "Condition": {
        "StringLike": {
          "kms:ViaService": [
            "sqs.${AWS_REGION}.amazonaws.com",
            "s3.${AWS_REGION}.amazonaws.com"
          ]
        }
      }
    }
  ]
}
POLICYEOF

# Create IAM role
echo "1️⃣ Creating IAM role..."
aws iam create-role \
    --role-name AureliaMWAAExecutionRole \
    --assume-role-policy-document file:///tmp/aurelia/mwaa-trust-policy.json \
    --tags Key=Project,Value=AURELIA Key=Lab,Value=Lab2 \
    2>/dev/null || echo "   Role may already exist, continuing..."

# Attach policy
echo "2️⃣ Attaching execution policy..."
aws iam put-role-policy \
    --role-name AureliaMWAAExecutionRole \
    --policy-name AureliaMWAAExecutionPolicy \
    --policy-document file:///tmp/aurelia/mwaa-execution-policy.json

# Wait for role to propagate
echo "3️⃣ Waiting for IAM role to propagate (10 seconds)..."
sleep 10

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name AureliaMWAAExecutionRole --query 'Role.Arn' --output text)

echo ""
echo "✅ MWAA Execution Role created!"
echo "   Role ARN: $ROLE_ARN"
echo ""

# Save role ARN
echo "export MWAA_EXECUTION_ROLE_ARN=$ROLE_ARN" >> infrastructure/vpc/network-config.env

# Also append to .env
echo "export MWAA_EXECUTION_ROLE_ARN=$ROLE_ARN" >> .env

echo "✅ Role configuration saved to:"
echo "   - infrastructure/vpc/network-config.env"
echo "   - .env"

# Cleanup temp files
rm -rf /tmp/aurelia

echo ""
echo "Next step: ./scripts/create_mwaa_environment.sh"
