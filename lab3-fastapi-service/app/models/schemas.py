"""
Pydantic schemas for API request/response validation
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class QueryRequest(BaseModel):
    """
    Request model for query endpoint
    """
    concept_name: str = Field(
        ...,
        description="Name of the financial concept to query",
        min_length=1,
        max_length=200
    )
    top_k: int = Field(
        default=5,
        description="Number of top chunks to retrieve",
        ge=1,
        le=50
    )

    class Config:
        json_schema_extra = {
            "example": {
                "concept_name": "revenue recognition",
                "top_k": 5
            }
        }


class RetrievedChunk(BaseModel):
    """
    Model for a retrieved chunk
    """
    content: str = Field(..., description="Content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    score: Optional[float] = Field(None, description="Similarity score")


class QueryResponse(BaseModel):
    """
    Response model for query endpoint
    """
    concept_name: str = Field(..., description="The queried concept name")
    retrieved_chunks: List[RetrievedChunk] = Field(
        ...,
        description="List of retrieved chunks"
    )
    source: str = Field(..., description="Source of the data")
    generated_note: Dict[str, Any] = Field(
        ...,
        description="Generated concept note with metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class SeedRequest(BaseModel):
    """
    Request model for seed endpoint
    """
    concept_name: str = Field(
        ...,
        description="Name of the financial concept to seed",
        min_length=1,
        max_length=200
    )
    force_refresh: bool = Field(
        default=False,
        description="Force refresh even if concept already exists"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "concept_name": "revenue recognition",
                "force_refresh": False
            }
        }


class SeedResponse(BaseModel):
    """
    Response model for seed endpoint
    """
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    concept_name: Optional[str] = Field(None, description="The seeded concept name")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Concept seeded successfully",
                "concept_name": "revenue recognition"
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response model
    """
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation Error",
                "detail": "concept_name is required"
            }
        }

class Citation(BaseModel):
    source_type: str = Field(..., description="pdf|wikipedia")
    title: Optional[str] = None
    page: Optional[int] = None
    url: Optional[str] = None
    score: Optional[float] = None

class ConceptNote(BaseModel):
    concept: str = Field(..., description="Canonical concept name")
    definition: str = Field(..., description="Precise, 2-4 sentence definition")
    intuition: str = Field(..., description="Plain-language intuition")
    formulae: List[str] = Field(default_factory=list, description="List of plaintext formulas")
    step_by_step: List[str] = Field(default_factory=list, description="Ordered steps to apply")
    pitfalls: List[str] = Field(default_factory=list, description="Common mistakes / caveats")
    examples: List[str] = Field(default_factory=list, description="Short examples or scenarios")
    citations: List[Citation] = Field(default_factory=list, description="Source traceability")
    used_fallback: bool = Field(default=False, description="True if Wikipedia fallback used")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp")