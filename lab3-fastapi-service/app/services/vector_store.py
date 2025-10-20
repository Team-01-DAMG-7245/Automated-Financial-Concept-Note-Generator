"""
Vector store integration with Pinecone/ChromaDB
This is a placeholder for integration with Lab 1's vector store
"""
import logging
from typing import List, Dict, Any
import pinecone
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector store wrapper for Pinecone
    """
    
    def __init__(self):
        """
        Initialize Pinecone connection
        """
        self.index = None
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """
        Initialize Pinecone client and index
        """
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment
            )
            
            # Connect to index
            if settings.pinecone_index_name in pinecone.list_indexes():
                self.index = pinecone.Index(settings.pinecone_index_name)
                logger.info(f"Connected to Pinecone index: {settings.pinecone_index_name}")
            else:
                logger.warning(f"Index {settings.pinecone_index_name} not found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise
    
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of query results with metadata
        """
        try:
            if not self.index:
                raise ValueError("Vector store not initialized")
            
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match["metadata"]
                }
                for match in results["matches"]
            ]
            
            logger.info(f"Retrieved {len(formatted_results)} results from vector store")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}")
            raise
    
    async def upsert(
        self,
        vectors: List[tuple],
        namespace: str = None
    ) -> None:
        """
        Upsert vectors into the index
        
        Args:
            vectors: List of (id, vector, metadata) tuples
            namespace: Optional namespace
        """
        try:
            if not self.index:
                raise ValueError("Vector store not initialized")
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=vectors,
                namespace=namespace
            )
            
            logger.info(f"Upserted {len(vectors)} vectors to vector store")
            
        except Exception as e:
            logger.error(f"Error upserting to vector store: {str(e)}")
            raise

