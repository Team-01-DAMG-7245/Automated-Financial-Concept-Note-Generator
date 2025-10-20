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
