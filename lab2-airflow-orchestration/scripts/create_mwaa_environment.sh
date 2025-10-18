#!/bin/bash

set -e

export AWS_PROFILE=aurelia
export AWS_REGION=us-east-1

# Load configs
source .env
source infrastructure/vpc/network-config.env

echo "🌪️  Creating MWAA Environment..."
echo ""

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get role ARN (try multiple sources)
if [ -z "$MWAA_EXECUTION_ROLE_ARN" ]; then
    ROLE_ARN=$(aws iam get-role --role-name AureliaMWAAExecutionRole --query 'Role.Arn' --output text 2>/dev/null)
else
    ROLE_ARN=$MWAA_EXECUTION_ROLE_ARN
fi

# Validate all required variables
if [ -z "$MWAA_BUCKET" ]; then
    echo "❌ MWAA_BUCKET not set!"
    exit 1
fi

if [ -z "$VPC_ID" ]; then
    echo "❌ VPC_ID not set!"
    exit 1
fi

if [ -z "$SUBNET_1" ] || [ -z "$SUBNET_2" ]; then
    echo "❌ Subnets not set!"
    exit 1
fi

if [ -z "$SECURITY_GROUP" ]; then
    echo "❌ SECURITY_GROUP not set!"
    exit 1
fi

if [ -z "$ROLE_ARN" ]; then
    echo "❌ MWAA Execution Role not found!"
    echo "   Run: ./scripts/create_mwaa_role.sh"
    exit 1
fi

echo "📋 Configuration:"
echo "   MWAA Bucket: $MWAA_BUCKET"
echo "   VPC: $VPC_ID"
echo "   Subnet 1: $SUBNET_1"
echo "   Subnet 2: $SUBNET_2"
echo "   Security Group: $SECURITY_GROUP"
echo "   Execution Role: $ROLE_ARN"
echo ""

echo "🚀 Creating MWAA environment..."
echo "   (This takes 20-30 minutes)"
echo ""

aws mwaa create-environment \
    --name aurelia-mwaa \
    --airflow-version "2.7.2" \
    --source-bucket-arn "arn:aws:s3:::${MWAA_BUCKET}" \
    --dag-s3-path "dags" \
    --requirements-s3-path "requirements.txt" \
    --execution-role-arn "$ROLE_ARN" \
    --network-configuration "SubnetIds=${SUBNET_1},${SUBNET_2},SecurityGroupIds=${SECURITY_GROUP}" \
    --logging-configuration '{
        "DagProcessingLogs": {"Enabled": true, "LogLevel": "INFO"},
        "SchedulerLogs": {"Enabled": true, "LogLevel": "INFO"},
        "TaskLogs": {"Enabled": true, "LogLevel": "INFO"},
        "WorkerLogs": {"Enabled": true, "LogLevel": "INFO"},
        "WebserverLogs": {"Enabled": true, "LogLevel": "INFO"}
    }' \
    --max-workers 2 \
    --environment-class "mw1.small" \
    --webserver-access-mode "PUBLIC_ONLY" \
    --tags Project=AURELIA,Lab=Lab2

echo ""
echo "✅ MWAA environment creation started!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏳ MWAA is now provisioning..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will take approximately 20-30 minutes."
echo ""
echo "📊 Monitor status:"
echo "   aws mwaa get-environment --name aurelia-mwaa --query 'Environment.Status'"
echo ""
echo "🔄 Watch continuously:"
echo "   watch -n 30 'aws mwaa get-environment --name aurelia-mwaa --query Environment.Status --output text'"
echo ""
echo "📈 Status progression:"
echo "   CREATING → AVAILABLE"
echo ""
echo "☕ Grab a coffee and check back in 20 minutes!"
