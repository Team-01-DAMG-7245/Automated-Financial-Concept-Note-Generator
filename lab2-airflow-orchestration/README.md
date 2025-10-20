# Lab 2 - AWS MWAA Orchestration

## Quick Start
```bash
# 1. Setup
aws configure --profile aurelia
source .env

# 2. Run scripts in order
./scripts/setup_s3_buckets.sh          # ~1 min
./scripts/create_mwaa_vpc.sh           # ~5 mins
./scripts/create_mwaa_environment.sh   # ~20 mins
./scripts/deploy_dags.sh               # ~1 min
```

## What Gets Created

### S3 Buckets (5)
- `aurelia-XXXXX-raw-pdfs` - Source PDFs
- `aurelia-XXXXX-processed-chunks` - Text chunks
- `aurelia-XXXXX-embeddings` - Vector embeddings
- `aurelia-XXXXX-concept-notes` - Generated notes
- `aurelia-XXXXX-mwaa` - Airflow DAGs/plugins

### VPC Infrastructure
- VPC: 10.0.0.0/16
- Private Subnets: 2 (us-east-1a, us-east-1b)
- Public Subnets: 2 (for NAT Gateways)
- NAT Gateways: 2
- Security Groups: 1

### MWAA Environment
- Airflow 2.7.3
- Auto-scaling workers
- CloudWatch logging

## DAGs

### fintbx_ingest_dag
**Schedule**: Weekly  
**Purpose**: Process PDF and create embeddings

**Tasks**:
1. Download PDF from S3
2. Parse and chunk (Lab 1 integration)
3. Generate embeddings
4. Store in vector DB

### concept_seed_dag
**Schedule**: On-demand  
**Purpose**: Pre-generate concept notes

**Concepts**: Duration, Sharpe Ratio, Black-Scholes, VaR, Beta, CAPM, etc.

## Environment Variables

Copy `.env.example` to `.env` and fill in:
```bash
export AWS_PROFILE=aurelia
export AWS_REGION=us-east-1
export OPENAI_API_KEY=your-key
export PINECONE_API_KEY=your-key
```

## Useful Commands
```bash
# Load environment
source .env

# Check S3 buckets
aws s3 ls | grep aurelia

# Check VPC
source infrastructure/vpc/network-config.env
echo $VPC_ID

# Get Airflow UI URL
aws mwaa get-environment --name aurelia-mwaa \
    --query 'Environment.WebserverUrl' --output text

# View logs
aws logs tail /aws/mwaa/environment/aurelia-mwaa/scheduler --follow
```

## Cost Estimate
- MWAA: ~$350/month
- NAT Gateways: ~$65/month  
- S3: ~$1/month
- **Total**: ~$400-450/month

Delete resources when done to avoid charges!
