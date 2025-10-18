#!/bin/bash

set -e

echo "🚀 Setting up Lab 2 - Airflow Orchestration"
echo ""

# Check we're in the right place
if [ ! -f "setup_lab2.sh" ]; then
    echo "❌ Please run this from lab2-airflow-orchestration directory"
    exit 1
fi

# Create all subdirectories
mkdir -p dags config scripts infrastructure/{iam,vpc,s3} plugins tests

echo "✅ Directory structure created"

# Create .env.example (template - don't commit actual .env)
cat > .env.example << 'ENVEOF'
# AWS Configuration
export AWS_PROFILE=aurelia
export AWS_REGION=us-east-1
export PROJECT_NAME=aurelia
export ENVIRONMENT=dev

# S3 Buckets (populate after creation)
export RAW_PDF_BUCKET=aurelia-XXXXX-raw-pdfs
export PROCESSED_BUCKET=aurelia-XXXXX-processed-chunks
export EMBEDDINGS_BUCKET=aurelia-XXXXX-embeddings
export CONCEPT_NOTES_BUCKET=aurelia-XXXXX-concept-notes
export MWAA_BUCKET=aurelia-XXXXX-mwaa

# OpenAI
export OPENAI_API_KEY=your-key-here

# Pinecone
export PINECONE_API_KEY=your-key-here
export PINECONE_ENVIRONMENT=us-east-1-aws
ENVEOF

echo "✅ Created .env.example template"

# Create requirements.txt
cat > requirements.txt << 'REQEOF'
# Core Airflow
apache-airflow==2.7.3
apache-airflow-providers-amazon==8.13.0
boto3==1.34.20

# RAG & LLM
langchain==0.1.0
langchain-openai==0.0.5
openai==1.7.2

# Vector Stores
pinecone-client==3.0.3
chromadb==0.4.22

# Structured Output
instructor==0.4.8
pydantic==2.5.3

# Database
psycopg2-binary==2.9.9

# Utilities
wikipedia==1.4.0
pandas==2.1.4
numpy==1.26.3
requests==2.31.0
REQEOF

echo "✅ Created requirements.txt"

# Create README
cat > README.md << 'MDEOF'
# Lab 2 - Airflow Orchestration

## Overview
Managed orchestration pipeline using AWS MWAA (Managed Workflows for Apache Airflow).

## Setup
1. Configure AWS credentials: `aws configure --profile aurelia`
2. Copy `.env.example` to `.env` and fill in values
3. Create S3 buckets: `./scripts/setup_s3_buckets.sh`
4. Create VPC: `./scripts/create_mwaa_vpc.sh`
5. Create MWAA environment: `./scripts/create_mwaa_environment.sh`
6. Deploy DAGs: `./scripts/deploy_dags.sh`

## Structure
- `dags/` - Airflow DAG definitions
- `config/` - Configuration files
- `scripts/` - Setup and deployment scripts
- `infrastructure/` - AWS infrastructure configs
- `plugins/` - Custom Airflow plugins
- `tests/` - Unit tests

## DAGs
- `fintbx_ingest_dag` - Process PDF and create embeddings
- `concept_seed_dag` - Seed concept database
MDEOF

echo "✅ Created README.md"

echo ""
echo "✅ Lab 2 setup complete!"
echo ""
echo "Next steps:"
echo "1. cp .env.example .env"
echo "2. Edit .env with your values"
echo "3. Create IAM policy in infrastructure/iam/"
echo "4. Run setup scripts from scripts/"
