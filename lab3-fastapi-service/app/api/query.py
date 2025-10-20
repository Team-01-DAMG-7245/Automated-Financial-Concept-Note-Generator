"""
Query endpoint router
"""
import logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import QueryRequest, QueryResponse, ErrorResponse
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize RAG service
rag_service = RAGService()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Concept Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Query for a financial concept",
    description="Retrieve relevant chunks and generate a concept note for the given financial concept"
)
async def query_concept(request: QueryRequest) -> QueryResponse:
    """
    Query endpoint to retrieve and generate concept notes
    
    Args:
        request: QueryRequest containing concept_name and top_k
        
    Returns:
        QueryResponse with retrieved chunks and generated note
        
    Raises:
        HTTPException: If query fails or concept not found
    """
    try:
        logger.info(f"Query received for concept: {request.concept_name}")
        
        # Query the RAG service
        result = await rag_service.query_concept(
            concept_name=request.concept_name,
            top_k=request.top_k
        )
        
        logger.info(f"Query successful for concept: {request.concept_name}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error for concept {request.concept_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error querying concept {request.concept_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query concept: {str(e)}"
        )

