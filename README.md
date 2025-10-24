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


---

## 🚀 Run Locally
```bash
cd lab4-streamlit-frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
Backend must be running first:

bash
Copy code
cd ../lab3-fastapi-service
uvicorn app.main:app --reload
Open: http://localhost:8501

🧠 Overview
Section	Description
📚 Query Concepts	Search and generate concept notes via the FastAPI /query endpoint.
📊 Database Explorer	View all seeded notes stored in PostgreSQL (or SQLite fallback).
📈 Evaluation Dashboard	Integrates Lab 5 metrics — latency plots, token cost, and accuracy charts.

🔗 API Endpoints Used
Method	Route	Purpose
POST	/query	Fetch or generate concept note
POST	/seed	Insert new financial concept into DB
GET	/health	Check FastAPI server status

⚙️ Features
Live Concept Querying: Real-time interaction with the RAG pipeline.

Caching & Retrieval: Fetches from DB first, regenerates if missing.

Interactive Visualization: Uses Plotly and Matplotlib for evaluation graphs.

Session State: Persists last searched concepts across tabs.

Seamless Backend Integration: Communicates with FastAPI JSON endpoints.

🧩 Requirements
bash
Copy code
streamlit
requests
pandas
plotly
matplotlib
sqlalchemy
psycopg2-binary
🖥️ Example Usage
bash
Copy code
# 1️⃣ Start backend
cd ../lab3-fastapi-service
uvicorn app.main:app --reload

# 2️⃣ Launch frontend
cd ../lab4-streamlit-frontend
streamlit run streamlit_app.py
Then visit: http://localhost:8501

# Lab 5 - Evaluation & Benchmarking
## Requirements Implemented
- **Req 19**: Quality metrics (accuracy, completeness, citation fidelity)
- **Req 20**: Latency comparison (cached vs generated)
- **Req 21**: Retrieval latency & token costs for Pinecone/ChromaDB

## Files
- `benchmark_suite.py` - Complete benchmarking framework
- `test_lab5.py` - Testing script for all requirements
- `evaluation_metrics.log` - Test run logs
- `results/` - Benchmark outputs and reports

## Usage
```bash
# Run tests
python3 test_lab5.py

# Run full benchmark
python3 benchmark_suite.py

# Generate plots
python3 generate_plots.py
```

## Results
- Quality Scores: 80% accuracy, 80% completeness, 100% citation fidelity
- Performance: 27x speedup with caching (15ms cached vs 410ms generated)
- Cost: ~$0.000008 per query using text-embedding-3-large

## Dependencies
```
pandas
matplotlib
aiohttp
openai
pinecone-client
chromadb
requests
```
