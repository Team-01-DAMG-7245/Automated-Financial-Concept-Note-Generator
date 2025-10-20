# AURELIA FastAPI RAG Service - Lab 3

A high-performance Retrieval-Augmented Generation (RAG) service for generating financial concept notes using FastAPI, Pinecone vector database, and OpenAI embeddings.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
If you have Pinecone and OpenAI API keys, add them to a `.env` file:
```bash
PINECONE_API_KEY=your_pinecone_key
OPENAI_API_KEY=your_openai_key
```

### 3. Run the Service
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

That's it! The service will run with mock data if API keys are not configured.

---

## Features

- ✅ **Query Endpoint**: Retrieve relevant chunks and generate concept notes
- ✅ **Seed Endpoint**: Populate the vector database with concept embeddings
- ✅ **Health Check**: Monitor service status
- ✅ **Pinecone Integration**: Vector database for semantic search (Lab 1)
- ✅ **OpenAI Embeddings**: text-embedding-3-large model
- ✅ **Async/Await**: Full async support for optimal performance
- ✅ **Type Safety**: Pydantic models for request/response validation
- ✅ **CORS Support**: Configurable CORS middleware
- ✅ **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Project Structure

```
lab3-fastapi-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API routers
│   │   ├── __init__.py
│   │   ├── query.py           # Query endpoint
│   │   └── seed.py            # Seed endpoint
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   └── schemas.py         # Request/response schemas
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── rag_service.py     # RAG service implementation
│   │   ├── pinecone_service.py # Pinecone integration
│   │   └── vector_store.py    # Vector store wrapper
│   └── core/                   # Configuration
│       ├── __init__.py
│       └── config.py          # Application settings
├── requirements.txt            # Python dependencies
├── run.py                      # Simple run script
├── test_api.py                # API test script
├── test_pinecone.py           # Pinecone test script
├── PINECONE_INTEGRATION.md    # Pinecone integration guide
└── README.md                  # This file
```

## 📋 Detailed Installation

### Prerequisites
- Python 3.11+
- pip
- (Optional) Pinecone API key
- (Optional) OpenAI API key

### Step-by-Step Setup

#### 1. Navigate to Project Directory
```bash
cd lab3-fastapi-service
```

#### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables (Optional)
Create a `.env` file in the project root:
```bash
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=fintbx-embeddings

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

**Note**: If you don't configure API keys, the service will run with mock data.

## 🏃 Running the Service

### Development Mode (Recommended for Testing)

**Option 1: Using uvicorn directly**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2: Using run.py**
```bash
python run.py
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points
Once running, the service is available at:
- 🌐 **API**: http://localhost:8000
- 📚 **Interactive Docs (Swagger)**: http://localhost:8000/docs
- 📖 **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- ❤️ **Health Check**: http://localhost:8000/health

## API Endpoints

### Health Check
```http
GET /health
```

### Query Concept
```http
POST /api/v1/query
Content-Type: application/json

{
  "concept_name": "revenue recognition",
  "top_k": 5
}
```

**Response**:
```json
{
  "concept_name": "revenue recognition",
  "retrieved_chunks": [
    {
      "content": "Revenue recognition is a key accounting principle...",
      "metadata": {"page": 1, "section": "Revenue"},
      "score": 0.95
    }
  ],
  "source": "Pinecone Vector DB",
  "generated_note": {
    "title": "Revenue Recognition",
    "summary": "Overview of revenue recognition principles...",
    "key_points": ["Point 1", "Point 2"]
  }
}
```

### Seed Concept
```http
POST /api/v1/seed
Content-Type: application/json

{
  "concept_name": "revenue recognition",
  "force_refresh": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Concept 'revenue recognition' seeded successfully",
  "concept_name": "revenue recognition"
}
```

## 🧪 Testing

### Test the API

**1. Test all endpoints:**
```bash
python test_api.py
```

**2. Test Pinecone integration:**
```bash
python test_pinecone.py
```

### Manual Testing with cURL

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Query Concept:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"concept_name\": \"revenue recognition\", \"top_k\": 5}"
```

**Seed Concept:**
```bash
curl -X POST "http://localhost:8000/api/v1/seed" \
  -H "Content-Type: application/json" \
  -d "{\"concept_name\": \"revenue recognition\", \"force_refresh\": false}"
```

### Testing with PowerShell (Windows)

**Health Check:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

**Query Concept:**
```powershell
$body = @{ concept_name = "revenue recognition"; top_k = 5 } | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/v1/query `
  -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

### Using Python

```python
import httpx

async def query_concept():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/query",
            json={"concept_name": "revenue recognition", "top_k": 5}
        )
        return response.json()

# Run
import asyncio
result = asyncio.run(query_concept())
print(result)
```

## Architecture

### Separation of Concerns

- **Routers** (`app/api/`): Handle HTTP requests and responses
- **Services** (`app/services/`): Business logic and data processing
- **Models** (`app/models/`): Pydantic schemas for validation
- **Core** (`app/core/`): Configuration and utilities

### Async/Await Patterns

All I/O operations use async/await for optimal performance:
- Database queries
- API calls
- File operations
- Embedding generation

## Error Handling

The service includes comprehensive error handling:
- **400 Bad Request**: Invalid input parameters
- **404 Not Found**: Concept not found
- **500 Internal Server Error**: Server-side errors

All errors return standardized error responses:
```json
{
  "error": "Error Type",
  "detail": "Detailed error message"
}
```

## Logging

Logging is configured at the application level with:
- Timestamp
- Logger name
- Log level
- Message

Logs include:
- Request/response information
- Error details
- Performance metrics

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Application Settings
ENVIRONMENT=development
DEBUG=true

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=fintbx-embeddings
PINECONE_ENVIRONMENT=us-east-1

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# RAG Settings
DEFAULT_TOP_K=5
MAX_TOP_K=50
```

### Pinecone Integration

The service is pre-configured to connect to the Lab 1 Pinecone index (`fintbx-embeddings`).

**To use Pinecone:**
1. Add your `PINECONE_API_KEY` to `.env`
2. Restart the service
3. Run `python test_pinecone.py` to verify connection

**Without Pinecone:**
- Service will run with mock data
- All endpoints remain functional
- No API keys required

## 📊 Expected Behavior

### With Pinecone Connected
- Queries use real vector search
- Results filtered by similarity threshold (0.7)
- Source: "Pinecone Vector DB"

### Without Pinecone (Mock Mode)
- Queries return mock data
- Source: "Mock Data (Pinecone not connected)"
- No API calls made

## 🐛 Troubleshooting

### Service won't start
```bash
# Check if port 8000 is available
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### No Pinecone results
- Check API key is correct
- Verify index name matches Lab 1
- Lower similarity threshold in `pinecone_service.py` (line 37)
- Run `python test_pinecone.py` to diagnose

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set
- Check API key is valid
- Ensure sufficient credits

## 📚 Documentation

- **Pinecone Integration**: See `PINECONE_INTEGRATION.md`
- **API Documentation**: http://localhost:8000/docs
- **Lab 1 Integration**: See Lab 1 README
- **Lab 2 Integration**: See Lab 2 README

## 🎯 Next Steps

1. ✅ **Service Running**: Basic FastAPI service operational
2. ✅ **Pinecone Integration**: Connected to Lab 1 index
3. 🔄 **LLM Integration**: Add OpenAI/Anthropic for note generation
4. 🔄 **Airflow Integration**: Connect to Lab 2 orchestration
5. 🔄 **Authentication**: Add API key or JWT authentication
6. 🔄 **Monitoring**: Add metrics and logging

## 📝 Notes

- Service uses mock data by default (no API keys required)
- Pinecone integration is optional but recommended
- All endpoints are functional with or without Pinecone
- Test scripts verify functionality

## 📄 License

Part of the AURELIA project for DAGM 7245.

---

**Quick Reference:**
- Start: `uvicorn app.main:app --reload`
- Test API: `python test_api.py`
- Test Pinecone: `python test_pinecone.py`
- Docs: http://localhost:8000/docs

