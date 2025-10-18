# Project AURELIA: Automated Financial Concept Note Generator

## Overview
AURELIA is a production-grade microservice that automatically generates standardized concept notes for financial topics using a Retrieval-Augmented Generation (RAG) approach. The system extracts and processes content from the Financial Toolbox User's Guide (fintbx.pdf) and falls back to Wikipedia for concepts not found in the corpus.

## Assignment Structure

### Lab 1 — PDF Corpus Construction ✓
Parse fintbx.pdf using PyMuPDF + pdfplumber + Tesseract OCR to extract:
- ✅ Text content (preserving reading order)
- ✅ Figures and images (separated from formulas)
- ✅ Formula images (extracted separately)
- ✅ Formulas and equations (with OCR)
- ✅ Code snippets (MATLAB code detection)
- ✅ Headings (document structure)
- ✅ Captions (for figures and tables)


### Lab 1.5 — Chunking Pipeline ✓
Implemented 5 chunking strategies with comprehensive evaluation:
- ✅ **Base Framework**: Abstract chunker with utilities
- ✅ **Strategy 1**: RecursiveCharacterTextSplitter (general-purpose)
- ✅ **Strategy 2**: MarkdownHeaderTextSplitter (structure-aware)
- ✅ **Strategy 3**: CodeAwareChunker (code preservation)
- ✅ **Strategy 4**: SemanticSectionChunker (concept-aware)
- ✅ **Strategy 5**: HybridChunker (intelligent routing) ⭐


### Lab 1.6 — Embeddings Module ✓
OpenAI text-embedding-3-large integration with advanced features:
- ✅ **Batch Processing**: 100 chunks per API call
- ✅ **Retry Logic**: Exponential backoff for rate limits
- ✅ **Cost Tracking**: Real-time cost estimation and logging
- ✅ **Caching**: Avoid reprocessing with disk cache
- ✅ **Progress Bar**: Visual progress for 3,462 pages
- ✅ **Validation**: Embedding validation and error handling


### Lab 1.7 — Pinecone Storage ✓
Pinecone vector database integration with advanced features:
- ✅ **Index Management**: Create/connect to Pinecone indexes
- ✅ **Batch Upsert**: 100 vectors per batch with progress tracking
- ✅ **Namespacing**: Organize by topic/section
- ✅ **Query Functions**: Query by text or vector
- ✅ **Error Handling**: Connection retry logic
- ✅ **Statistics**: Track upsert progress and latency

### Lab 2 — Vector Store Setup (Pinecone/ChromaDB)
- Create vector embeddings for PDF corpus
- Namespace by topic headings
- Store in Pinecone or ChromaDB

### Lab 3 — Concept DB Seeder Pipeline (Airflow)
- Airflow DAG for concept seeding
- Generate structured JSON using instructor package
- Cache concepts for reuse

### Lab 4 — RAG Service (FastAPI)
- `/query` endpoint for retrieval and generation
- `/seed` endpoint for concept updates
- Primary source: fintbx.pdf corpus

### Lab 5 — Streamlit Frontend
- User interface for concept queries
- View cached concept notes
- Trigger new note generation

### Lab 6 — Wikipedia Fallback Layer
- Fetch Wikipedia content when concept not in corpus
- Standardize through instructor model
- Maintain consistent note structure

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Lab 1 - PDF Parsing
```bash
cd Automated-Financial-Concept-Note-Generator
python src/parse_fintbx.py --output data/parsed
```

### 3. Run Lab 1.5 - Chunking Pipeline
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

### 4. Run Lab 1.6 - Generate Embeddings
```bash
# Set OpenAI API key
$env:OPENAI_API_KEY="your-api-key-here"

# Test embedder with sample chunks
python src/embeddings/embedder.py

# Embed hybrid chunks (production)
python src/embeddings/embed_hybrid_chunks.py
```

### 5. Run Lab 1.7 - Upload to Pinecone
```bash
# Set Pinecone API key
$env:PINECONE_API_KEY="your-api-key-here"

# Test Pinecone store
python src/storage/pinecone_store.py

# Upload embedded chunks to Pinecone
python src/storage/upload_to_pinecone.py
```

### 6. Expected Output Structure
```
data/
├── raw/
│   └── fintbx.pdf     # Original PDF
└── parsed/
    ├── text/           # Page-by-page text content + all_text_blocks.json
    ├── figures/        # Figure metadata + images/
    │   └── images/     # Regular figures/diagrams
    ├── formulas/       # Formula images + text
    │   └── images/     # Equation/formula images
    ├── code/           # Code snippets (MATLAB)
    ├── headings/       # Document headings
    └── metadata/       # Corpus metadata
```

### 7. Chunking Output Structure
```
outputs/
├── fintbx_complete.md              # Complete markdown (174K lines)
├── fintbx_metadata.json            # Document metadata
├── chunks/                         # Chunked data
│   ├── chunks_recursive.json
│   ├── chunks_markdown.json
│   ├── chunks_code_aware.json
│   ├── chunks_semantic.json
│   └── chunks_hybrid.json
├── chunking_tests/                 # Strategy tests
│   ├── recursive_benchmark.json
│   ├── markdown_header_hierarchy_stats.json
│   ├── code_aware_validation.json
│   ├── semantic_concept_coverage.json
│   └── hybrid_chunker_test.json
└── chunking_evaluation/            # Evaluation reports
    ├── chunking_evaluation.json
    └── chunking_evaluation.md
```

### 8. Embeddings Output Structure
```
outputs/
├── embeddings_cache/
│   └── embeddings_cache.json       # Cached embeddings
├── embeddings_stats.json           # Embedding statistics
└── chunks/
    └── chunks_hybrid_embedded.json # Chunks with embeddings
```

### 9. Pinecone Storage Output Structure
```
outputs/
└── pinecone_stats.json             # Pinecone statistics

Pinecone Index:
├── fintbx-embeddings (default namespace)
│   └── 3072-dimensional vectors
└── Optional namespaces:
    ├── portfolio-theory
    ├── risk-metrics
    └── code-examples
```

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

## Project Status
- [x] Lab 1: PDF Corpus Construction
- [x] Lab 1.5: Chunking Pipeline (5 strategies evaluated)
- [x] Lab 1.6: Embeddings Module (text-embedding-3-large)
- [x] Lab 1.7: Pinecone Storage (vector database)
- [ ] Lab 2: Vector Store Setup (Complete!)
- [ ] Lab 3: Airflow DAG
- [ ] Lab 4: FastAPI Service
- [ ] Lab 5: Streamlit Frontend
- [ ] Lab 6: Wikipedia Fallback

## Notes
- **Reading Order**: Preserved using PyMuPDF text blocks
- **Captions**: Automatically extracted for figures and tables
- **Formula Detection**: Separates formula images from regular figures
- **Code Detection**: Identifies MATLAB code snippets using regex patterns
- **OCR**: Tesseract OCR for formula extraction (optional)
- **Performance**: ~165 pages/second processing speed
- **Content Organization**: All content types stored in separate folders for efficient RAG retrieval

