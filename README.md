# AURELIA - Automated Financial Concept Note Generator

Production-grade RAG system for generating standardized concept notes from financial documentation.

## Project Structure
```
├── lab1-pdf-processing/           # PDF parsing, chunking, embeddings
├── lab2-airflow-orchestration/    # AWS MWAA orchestration
├── lab3-fastapi-service/          # RAG API (future)
└── lab4-streamlit-frontend/       # User interface (future)
```

## Lab 1: PDF Processing ✅

### Quick Start
```bash
cd lab1-pdf-processing
pip install -r requirements.txt
python pipeline_orchestrator.py --output-dir outputs
```

### Pipeline Options
```bash
# Complete pipeline (PDF → Vector DB)
python pipeline_orchestrator.py --output-dir outputs

# Pipeline 1: PDF → Markdown (~1 hour)
python pipeline_orchestrator.py --pipeline 1 --output-dir outputs

# Pipeline 2: Markdown → Embeddings (~10 seconds)
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs
```

### Chunking Strategy
**Hybrid Chunker** - Intelligently routes content:
- Narrative → MarkdownHeaderSplitter
- Code → CodeAwareChunker
- Formulas → SemanticSectionChunker
- Mixed → RecursiveCharacterSplitter

---

## Lab 2: AWS MWAA Orchestration 🚧

### Setup Steps
```bash
cd lab2-airflow-orchestration

# 1. Configure AWS
aws configure --profile aurelia
source .env

# 2. Create S3 buckets
./scripts/setup_s3_buckets.sh

# 3. Create VPC (~5 mins)
./scripts/create_mwaa_vpc.sh

# 4. Create MWAA environment (~20 mins)
./scripts/create_mwaa_environment.sh

# 5. Deploy DAGs
./scripts/deploy_dags.sh
```

### Infrastructure Created
- **5 S3 Buckets**: raw-pdfs, processed-chunks, embeddings, concept-notes, mwaa
- **VPC**: Private subnets (2), NAT Gateways (2), Security Groups
- **MWAA**: Airflow 2.7.3 environment with auto-scaling

### DAGs
1. **fintbx_ingest_dag** - Process PDF, create embeddings (weekly)
2. **concept_seed_dag** - Pre-generate concept notes (on-demand)

### Access Airflow UI
```bash
aws mwaa get-environment --name aurelia-mwaa \
    --query 'Environment.WebserverUrl' --output text
```

---

## Tech Stack
- **Orchestration**: Apache Airflow (AWS MWAA)
- **Vector DB**: Pinecone / ChromaDB
- **LLM**: OpenAI GPT-4 + text-embedding-3-large
- **Structured Output**: Instructor
- **Cloud**: AWS (S3, MWAA, VPC, RDS)

## Security
- Never commit `.env` files
- Never commit AWS credentials
- Rotate API keys regularly

## Documentation
- Lab 1: See `lab1-pdf-processing/HYBRID_CHUNKING_JUSTIFICATION.md`
- Lab 2: See `lab2-airflow-orchestration/README.md`
