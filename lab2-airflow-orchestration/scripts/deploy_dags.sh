#!/bin/bash

set -e

export AWS_PROFILE=aurelia
source .env

echo "📤 Deploying DAGs to MWAA..."
echo ""

# Check MWAA status first
STATUS=$(aws mwaa get-environment --name aurelia-mwaa --query 'Environment.Status' --output text)

if [ "$STATUS" != "AVAILABLE" ]; then
    echo "❌ MWAA is not available yet. Status: $STATUS"
    exit 1
fi

echo "✅ MWAA is AVAILABLE"
echo ""

# Check for DAG files
if [ ! -f "dags/fintbx_ingest_dag.py" ]; then
    echo "❌ fintbx_ingest_dag.py not found!"
    exit 1
fi

if [ ! -f "dags/concept_seed_dag.py" ]; then
    echo "❌ concept_seed_dag.py not found!"
    exit 1
fi

echo "📁 Found DAG files:"
ls -lh dags/*.py

echo ""
echo "🚀 Uploading to S3..."

# Upload DAGs
aws s3 cp dags/fintbx_ingest_dag.py s3://${MWAA_BUCKET}/dags/
aws s3 cp dags/concept_seed_dag.py s3://${MWAA_BUCKET}/dags/

echo ""
echo "✅ DAGs uploaded!"
echo ""

# Verify upload
echo "📋 Verifying upload:"
aws s3 ls s3://${MWAA_BUCKET}/dags/

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DAG Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "DAGs will appear in Airflow UI within 2-3 minutes"
echo ""
echo "🌐 Access Airflow UI:"
WEBSERVER_URL=$(aws mwaa get-environment --name aurelia-mwaa --query 'Environment.WebserverUrl' --output text)
echo "   https://${WEBSERVER_URL}"
echo ""
echo "Next steps:"
echo "  1. Open Airflow UI in browser"
echo "  2. Find your DAGs: fintbx_ingest_dag, concept_seed_dag"
echo "  3. Trigger a DAG manually to test"
echo "  4. Check task logs"
