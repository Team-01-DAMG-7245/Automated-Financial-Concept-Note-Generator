"""
Pinecone Vector Database Service for AURELIA RAG
Handles vector storage, retrieval, and similarity search operations
"""
import logging
import time
from typing import List, Dict, Any, Optional
import pinecone
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class PineconeConnectionError(Exception):
    """Custom exception for Pinecone connection errors"""
    pass


class PineconeQueryError(Exception):
    """Custom exception for Pinecone query errors"""
    pass


class PineconeService:
    """
    Service for interacting with Pinecone vector database
    Handles embeddings generation, vector storage, and similarity search
    """
    
    def __init__(self):
        """
        Initialize Pinecone service with configuration from settings
        """
        self.pc: Optional[Pinecone] = None
        self.index: Optional[pinecone.Index] = None
        self.openai_client: Optional[OpenAI] = None
        self.embedding_model: str = settings.embedding_model
        self.index_name: str = settings.pinecone_index_name
        self.similarity_threshold: float = 0.7
        self.max_retries: int = 3
        self.retry_delay: float = 1.0
        
        # Initialize connections
        self._initialize_connections()
    
    def _initialize_connections(self) -> None:
        """
        Initialize Pinecone and OpenAI clients
        """
        try:
            # Initialize Pinecone client
            if settings.pinecone_api_key:
                self.pc = Pinecone(api_key=settings.pinecone_api_key)
                logger.info("Pinecone client initialized successfully")
            else:
                logger.warning("PINECONE_API_KEY not set, using mock mode")
            
            # Initialize OpenAI client
            if settings.openai_api_key:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OPENAI_API_KEY not set, embedding generation will fail")
            
            # Connect to index if it exists
            if self.pc:
                self._connect_to_index()
                
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone service: {str(e)}")
            raise PineconeConnectionError(f"Initialization failed: {str(e)}")
    
    def _connect_to_index(self) -> None:
        """
        Connect to the Pinecone index
        """
        try:
            # List all indexes
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name in existing_indexes:
                self.index = self.pc.Index(self.index_name)
                logger.info(f"Connected to existing index: {self.index_name}")
                
                # Get index stats
                stats = self.index.describe_index_stats()
                logger.info(f"Index stats: {stats}")
            else:
                logger.warning(
                    f"Index '{self.index_name}' not found. "
                    f"Available indexes: {existing_indexes}"
                )
                
        except Exception as e:
            logger.error(f"Failed to connect to index: {str(e)}")
            raise PineconeConnectionError(f"Index connection failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test Pinecone connection and verify connectivity
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            if not self.pc:
                logger.error("Pinecone client not initialized")
                return False
            
            # List indexes to test connection
            indexes = self.pc.list_indexes()
            logger.info(f"Connection test successful. Found {len(list(indexes))} indexes")
            
            # Test index connection if available
            if self.index:
                stats = self.index.describe_index_stats()
                logger.info(f"Index connection verified: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    async def query_similar_chunks(
        self,
        concept_query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for similar chunks based on concept query
        
        Args:
            concept_query: The concept or query string to search for
            top_k: Number of top similar chunks to retrieve
            
        Returns:
            List of dictionaries containing:
                - chunk_text: The actual text content
                - metadata: section_title, page_number, document_source
                - similarity_score: The relevance score
            Empty list if no chunks meet the similarity threshold
            
        Raises:
            PineconeQueryError: If query operation fails
        """
        try:
            logger.info(f"Querying Pinecone for: '{concept_query}' (top_k={top_k})")
            
            # Check if index is available
            if not self.index:
                logger.warning("Pinecone index not available, returning empty results")
                return []
            
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(concept_query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Query Pinecone with retry logic
            results = await self._query_with_retry(
                query_vector=query_embedding,
                top_k=top_k
            )
            
            # Filter and format results
            filtered_results = self._filter_and_format_results(results)
            
            logger.info(
                f"Retrieved {len(results.get('matches', []))} results, "
                f"{len(filtered_results)} above threshold {self.similarity_threshold}"
            )
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            raise PineconeQueryError(f"Query failed: {str(e)}")
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using OpenAI API
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
            None if generation fails
        """
        try:
            if not self.openai_client:
                logger.warning("OpenAI client not available, using mock embedding")
                return self._generate_mock_embedding()
            
            logger.debug(f"Generating embedding for text: {text[:50]}...")
            
            # Use OpenAI's text-embedding-3-large model
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return None
    
    def _generate_mock_embedding(self) -> List[float]:
        """
        Generate a mock embedding for testing without OpenAI
        
        Returns:
            Mock embedding vector
        """
        # Return a mock embedding with appropriate dimensions
        # text-embedding-3-large has 3072 dimensions
        return [0.1] * 3072
    
    async def _query_with_retry(
        self,
        query_vector: List[float],
        top_k: int
    ) -> Dict[str, Any]:
        """
        Query Pinecone with exponential backoff retry logic
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to retrieve
            
        Returns:
            Query results from Pinecone
            
        Raises:
            PineconeQueryError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Query attempt {attempt + 1}/{self.max_retries}")
                
                # Query Pinecone
                results = self.index.query(
                    vector=query_vector,
                    top_k=top_k,
                    include_metadata=True
                )
                
                logger.debug(f"Query successful on attempt {attempt + 1}")
                return results
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Query attempt {attempt + 1} failed: {str(e)}"
                )
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await self._sleep(delay)
        
        # All retries failed
        logger.error(f"All {self.max_retries} query attempts failed")
        raise PineconeQueryError(
            f"Query failed after {self.max_retries} attempts: {str(last_exception)}"
        )
    
    async def _sleep(self, seconds: float) -> None:
        """
        Async sleep helper
        
        Args:
            seconds: Number of seconds to sleep
        """
        await asyncio.sleep(seconds)
    
    def _filter_and_format_results(
        self,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter results by similarity threshold and format output
        
        Args:
            results: Raw results from Pinecone
            
        Returns:
            List of formatted and filtered results
        """
        formatted_results = []
        
        for match in results.get('matches', []):
            # Extract similarity score
            score = match.get('score', 0.0)
            
            # Filter by threshold
            if score < self.similarity_threshold:
                logger.debug(
                    f"Skipping result with score {score:.3f} "
                    f"(threshold: {self.similarity_threshold})"
                )
                continue
            
            # Extract metadata
            metadata = match.get('metadata', {})
            
            # Format result
            formatted_result = {
                'chunk_text': metadata.get('text', ''),
                'metadata': {
                    'section_title': metadata.get('section_title', 'Unknown'),
                    'page_number': metadata.get('page_number', 0),
                    'document_source': metadata.get('document_source', 'Unknown'),
                    'chunk_id': metadata.get('chunk_id', ''),
                    'chunk_index': metadata.get('chunk_index', 0)
                },
                'similarity_score': score
            }
            
            formatted_results.append(formatted_result)
            
            logger.debug(
                f"Added result: score={score:.3f}, "
                f"section={metadata.get('section_title', 'Unknown')}"
            )
        
        return formatted_results
    
    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> None:
        """
        Upsert chunks into Pinecone index
        
        Args:
            chunks: List of chunk dictionaries with 'id', 'values', and 'metadata'
            namespace: Optional namespace for the vectors
        """
        try:
            if not self.index:
                logger.error("Pinecone index not available")
                raise PineconeConnectionError("Index not connected")
            
            logger.info(f"Upserting {len(chunks)} chunks to index")
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                logger.debug(f"Upserted batch {i//batch_size + 1}")
            
            logger.info("Successfully upserted all chunks")
            
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {str(e)}")
            raise PineconeQueryError(f"Upsert failed: {str(e)}")
    
    def delete_chunks(
        self,
        chunk_ids: List[str],
        namespace: Optional[str] = None
    ) -> None:
        """
        Delete chunks from Pinecone index
        
        Args:
            chunk_ids: List of chunk IDs to delete
            namespace: Optional namespace
        """
        try:
            if not self.index:
                logger.error("Pinecone index not available")
                raise PineconeConnectionError("Index not connected")
            
            logger.info(f"Deleting {len(chunk_ids)} chunks from index")
            
            self.index.delete(ids=chunk_ids, namespace=namespace)
            
            logger.info("Successfully deleted chunks")
            
        except Exception as e:
            logger.error(f"Failed to delete chunks: {str(e)}")
            raise PineconeQueryError(f"Delete failed: {str(e)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index
        
        Returns:
            Dictionary with index statistics
        """
        try:
            if not self.index:
                logger.error("Pinecone index not available")
                return {}
            
            stats = self.index.describe_index_stats()
            return dict(stats)
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {}


# Import asyncio for async sleep
import asyncio

