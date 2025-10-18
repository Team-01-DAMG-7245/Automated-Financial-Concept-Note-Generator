# Project AURELIA: Automated Financial Concept Note Generator

## Overview
AURELIA is a production-grade microservice that automatically generates standardized concept notes for financial topics using a Retrieval-Augmented Generation (RAG) approach. The system extracts and processes content from the Financial Toolbox User's Guide (fintbx.pdf) and falls back to Wikipedia for concepts not found in the corpus.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Lab 1.1 - PDF Parsing
```bash
cd Automated-Financial-Concept-Note-Generator
python src/parse_fintbx.py --output data/parsed
```

### 3. Run Lab 1.2 - Chunking Pipeline
```bash
# Test individual chunking strategies
python src/chunkers/recursive_chunker.py
python src/chunkers/markdown_header_chunker.py
python src/chunkers/code_aware_chunker.py
python src/chunkers/semantic_section_chunker.py

# Test hybrid chunking strategy (recommended)
python src/chunkers/hybrid_chunker.py

# Run comprehensive evaluation
python src/chunkers/evaluator.py
```

### 4. Run Lab 1.3 - Generate Embeddings
```bash
# Set OpenAI API key
$env:OPENAI_API_KEY="your-api-key-here"

# Test embedder with sample chunks
python src/embeddings/embedder.py

# Embed hybrid chunks (production)
python src/embeddings/embed_hybrid_chunks.py
```

### 5. Run Lab 1.4 - Upload to Pinecone
```bash
# Set Pinecone API key
$env:PINECONE_API_KEY="your-api-key-here"

# Test Pinecone store
python src/storage/pinecone_store.py

# Upload embedded chunks to Pinecone
python src/storage/upload_to_pinecone.py
```

### 6. Pipeline Orchestrator (`pipeline_orchestrator.py`)

**Purpose**: Coordinate all processing steps from PDF to vector database.

**Features**:
- ✅ Two separate pipelines for flexibility
- ✅ Progress tracking and logging
- ✅ Checkpoint system for error recovery
- ✅ Performance metrics collection
- ✅ Dry-run mode for testing

**Pipeline 1: PDF → Markdown** (Takes ~1 hour)
```bash
python pipeline_orchestrator.py --pipeline 1 --output-dir outputs
```
- Parse PDF using multiple techniques
- Generate structured markdown
- Save to `outputs/fintbx_complete.md`

**Pipeline 2: Markdown → Chunks → Embeddings → Storage** (Fast, ~10 seconds)
```bash
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs
```
- Load markdown file
- Apply chunking strategy
- Generate embeddings
- Store in Pinecone

**Complete Pipeline**:
```bash
python pipeline_orchestrator.py --output-dir outputs
```

**Additional Options**:
```bash
# Try different chunking strategies
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs --chunker recursive
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs --chunker markdown
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs --chunker code

# Dry run (validate configuration)
python pipeline_orchestrator.py --pipeline 1 --dry-run
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs --dry-run

# Resume from checkpoint
python pipeline_orchestrator.py --resume
```

## Pipeline Orchestrator

**File**: `pipeline_orchestrator.py`

**Purpose**: Coordinate all processing steps from PDF to vector database.

### Two Separate Pipelines

#### Pipeline 1: PDF → Markdown (Takes ~1 hour)
```bash
python pipeline_orchestrator.py --pipeline 1 --output-dir outputs
```

**Steps**:
1. Parse PDF using multiple techniques
2. Generate structured markdown
3. Save to `outputs/fintbx_complete.md`

#### Pipeline 2: Markdown → Chunks → Embeddings → Storage (Fast, ~10 seconds)
```bash
python pipeline_orchestrator.py --pipeline 2 --output-dir outputs
```

**Steps**:
1. Load markdown file
2. Apply chunking strategy
3. Generate embeddings
4. Store in Pinecone

### Complete Pipeline
```bash
python pipeline_orchestrator.py --output-dir outputs
```

**Runs all steps in sequence**.


## Chunking Strategy Comparison

### Recommended: Hybrid Chunker ⭐

The hybrid approach intelligently routes content to the optimal chunker:

| Content Type | Routing Strategy | Why |
|--------------|------------------|-----|
| **Narrative Text** | MarkdownHeaderTextSplitter | Preserves structure & hierarchy |
| **Code Blocks** | CodeAwareChunker | 100% code preservation |
| **Mathematical Formulas** | SemanticSectionChunker | Concept-aware chunking |
| **Mixed Content** | RecursiveCharacterTextSplitter | Balanced approach |

**Benefits:**
- ✅ Intelligent content detection
- ✅ Best of all strategies
- ✅ 100% code preservation where needed
- ✅ Structure awareness for narrative
- ✅ Semantic coherence for formulas
- ✅ Fast processing overall

See `HYBRID_CHUNKING_JUSTIFICATION.md` for detailed analysis.

## Deployment Requirements
- All services must run on managed cloud platform (GCP/AWS)
- No local components allowed
- Use Cloud Run, App Engine, or EC2/Elastic Beanstalk
- Airflow, databases, and applications must be cloud-hosted

## Technology Stack
- **Parser**: PyMuPDF (fitz) + pdfplumber + Tesseract OCR
- **Vector Store**: Pinecone
- **Orchestration**: Apache Airflow
- **API**: FastAPI
- **Frontend**: Streamlit
- **LLM**: OpenAI (via LangChain)
- **Structured Output**: Instructor package
- **Fallback**: Wikipedia API

\
# Lab 2 - Airflow Orchestration

## Overview
Managed orchestration pipeline using AWS MWAA.

## Quick Start
1. Configure AWS: `aws configure --profile aurelia`
2. Create S3 buckets: `./scripts/setup_s3_buckets.sh`
3. Create VPC: `./scripts/create_mwaa_vpc.sh`
4. Deploy DAGs: `./scripts/deploy_dags.sh`

## Structure
- `dags/` - Airflow DAG files
- `scripts/` - Setup scripts
- `infrastructure/` - AWS configs
- `config/` - Configuration files