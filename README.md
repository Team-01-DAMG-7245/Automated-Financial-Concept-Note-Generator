# 🧠 AURELIA – Automated Financial Concept Note Generator

Retrieval-Augmented Generation (RAG) system that turns financial documents into structured, standardized concept notes.

## 📂 Structure
```
├── lab1-pdf-processing/        # PDF → Markdown → Embeddings
├── lab2-airflow-orchestration/ # AWS MWAA orchestration
├── lab3-fastapi-service/       # FastAPI RAG microservice
└── lab4-streamlit-frontend/    # (upcoming) UI
```

## ✅ Lab 1 – PDF Processing
```bash
cd lab1-pdf-processing
pip install -r requirements.txt
python pipeline_orchestrator.py --output-dir outputs
```
Hybrid chunking via `MarkdownHeaderSplitter`, `CodeAwareChunker`, and `SemanticSectionChunker`.

## ☁️ Lab 2 – AWS MWAA Orchestration
Creates S3 buckets, VPC, and Airflow 2.7 environment for automated ingestion.  
DAGs:  
- `fintbx_ingest_dag` → weekly PDF → embeddings  
- `concept_seed_dag` → on-demand concept seeding  

## ⚡ Lab 3 – FastAPI RAG Service
```bash
cd lab3-fastapi-service
pip install -r requirements.txt
uvicorn app.main:app --reload
```
`.env` example:
```
OPENAI_API_KEY=sk-********
DATABASE_URL=postgresql+psycopg://aurelia:pgpass@localhost:5433/aurelia_db
PINECONE_API_KEY=********
```

**Endpoints**
| Method | Route | Purpose |
|--------|-------|----------|
| GET | `/health` | Health check |
| POST | `/api/v1/query` | Query & generate note |
| POST | `/api/v1/seed` | Pre-seed concept |

**Example**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/query  -H "Content-Type: application/json"  -d '{"concept_name": "revenue recognition"}'
```

**Sample Output (truncated)**
```json
{
  "concept_name": "revenue recognition",
  "source": "wikipedia (Fallback)",
  "generated_note": {
    "concept": "Revenue Recognition",
    "definition": "Revenue recognition determines when income becomes realized..."
  }
}
```

## 🧰 Stack
FastAPI · SQLAlchemy · OpenAI GPT-4 + Instructor · Pinecone/ChromaDB · PostgreSQL · Airflow (MWAA)
