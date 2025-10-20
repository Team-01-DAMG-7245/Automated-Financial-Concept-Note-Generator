"""
Seed endpoint router
"""
import logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import SeedRequest, SeedResponse, ErrorResponse
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize RAG service
rag_service = RAGService()


@router.post(
    "/seed",
    response_model=SeedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Seed a financial concept",
    description="Seed the database with embeddings for a specific financial concept"
)
async def seed_concept(request: SeedRequest) -> SeedResponse:
    """
    Seed endpoint to populate the vector database with concept embeddings
    
    Args:
        request: SeedRequest containing concept_name and force_refresh flag
        
    Returns:
        SeedResponse with success status and message
        
    Raises:
        HTTPException: If seeding fails
    """
    try:
        logger.info(f"Seed request received for concept: {request.concept_name}")
        
        # Seed the concept
        result = await rag_service.seed_concept(
            concept_name=request.concept_name,
            force_refresh=request.force_refresh
        )
        
        logger.info(f"Seed successful for concept: {request.concept_name}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error for concept {request.concept_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error seeding concept {request.concept_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed concept: {str(e)}"
        )

