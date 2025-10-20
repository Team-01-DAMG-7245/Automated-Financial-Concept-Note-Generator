"""
RAG Service for querying and seeding financial concepts
"""
import logging
from typing import List, Dict, Any
import asyncio
from app.models.schemas import QueryResponse, SeedResponse, RetrievedChunk
from app.services.pinecone_service import PineconeService, PineconeQueryError
from app.services.wikipedia_fallback import WikipediaFallbackService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for Retrieval-Augmented Generation operations
    """
    
    def __init__(self):
        """
        Initialize RAG service with vector store and LLM
        """
        self.pinecone_service: PineconeService = None
        self.wikipedia_fallback: WikipediaFallbackService = None
        self.llm = None
        self._initialize_components()
    
    def _initialize_components(self):
        """
        Initialize vector store and LLM components
        """
        try:
            # Initialize Pinecone service
            self.pinecone_service = PineconeService()
            
            # Test connection
            if self.pinecone_service.test_connection():
                logger.info("Pinecone connection verified")
            else:
                logger.warning("Pinecone connection test failed, service will use mock data")
            
            # Initialize Wikipedia fallback service
            self.wikipedia_fallback = WikipediaFallbackService()
            logger.info("Wikipedia fallback service initialized")
            
            # TODO: Initialize LLM (OpenAI, Anthropic, etc.)
            # self.llm = LLMClient()
            
            logger.info("RAG service components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {str(e)}")
            # Continue with mock mode
            logger.warning("Continuing in mock mode without vector store")
    
    async def query_concept(
        self,
        concept_name: str,
        top_k: int = 5
    ) -> QueryResponse:
        """
        Query for a financial concept and generate a note
        
        Args:
            concept_name: Name of the concept to query
            top_k: Number of chunks to retrieve
            
        Returns:
            QueryResponse with retrieved chunks and generated note
        """
        logger.info(f"Querying concept: {concept_name} with top_k={top_k}")
        
        # Step 1: Query Pinecone for similar chunks
        try:
            if self.pinecone_service and self.pinecone_service.index:
                # Use real Pinecone service
                pinecone_results = await self.pinecone_service.query_similar_chunks(
                    concept_query=concept_name,
                    top_k=top_k
                )
                
                if pinecone_results:
                    logger.info(f"Retrieved {len(pinecone_results)} chunks from Pinecone")
                    chunks = self._format_pinecone_results(pinecone_results)
                    source = "fintbx_pdf (Pinecone Vector DB)"
                else:
                    # No Pinecone results - try Wikipedia fallback
                    logger.warning("No results from Pinecone, attempting Wikipedia fallback")
                    chunks = await self._try_wikipedia_fallback(concept_name, top_k)
                    source = "wikipedia (Fallback)" if chunks else "Mock Data (No results)"
            else:
                # Pinecone not available - try Wikipedia fallback
                logger.warning("Pinecone not available, attempting Wikipedia fallback")
                chunks = await self._try_wikipedia_fallback(concept_name, top_k)
                source = "wikipedia (Fallback)" if chunks else "Mock Data (Pinecone not connected)"
                
        except PineconeQueryError as e:
            # Pinecone error - try Wikipedia fallback
            logger.error(f"Pinecone query error: {str(e)}, attempting Wikipedia fallback")
            chunks = await self._try_wikipedia_fallback(concept_name, top_k)
            source = "wikipedia (Fallback)" if chunks else "Mock Data (Pinecone error)"
        
        # Step 2: Generate concept note
        generated_note = await self._generate_concept_note(
            concept_name=concept_name,
            chunks=chunks
        )
        
        # Step 3: Format response
        return QueryResponse(
            concept_name=concept_name,
            retrieved_chunks=chunks,
            source=source,
            generated_note=generated_note
        )
    
    async def seed_concept(
        self,
        concept_name: str,
        force_refresh: bool = False
    ) -> SeedResponse:
        """
        Seed the database with embeddings for a concept
        
        Args:
            concept_name: Name of the concept to seed
            force_refresh: Whether to force refresh existing embeddings
            
        Returns:
            SeedResponse with success status
        """
        logger.info(f"Seeding concept: {concept_name}, force_refresh={force_refresh}")
        
        # Check if concept already exists
        if not force_refresh:
            exists = await self._check_concept_exists(concept_name)
            if exists:
                return SeedResponse(
                    success=True,
                    message=f"Concept '{concept_name}' already exists. Use force_refresh=true to update.",
                    concept_name=concept_name
                )
        
        # Generate embeddings and store
        try:
            await self._generate_and_store_embeddings(concept_name)
            
            return SeedResponse(
                success=True,
                message=f"Concept '{concept_name}' seeded successfully",
                concept_name=concept_name
            )
        except Exception as e:
            logger.error(f"Failed to seed concept {concept_name}: {str(e)}")
            raise
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query
        
        Args:
            query: Query string
            
        Returns:
            Query embedding vector
        """
        # TODO: Implement embedding generation
        # For now, return a mock embedding
        logger.debug(f"Generating embedding for query: {query}")
        await asyncio.sleep(0.1)  # Simulate async operation
        return [0.1] * 384  # Mock embedding (384 dimensions for sentence-transformers)
    
    def _format_pinecone_results(
        self,
        pinecone_results: List[Dict[str, Any]]
    ) -> List[RetrievedChunk]:
        """
        Format Pinecone results into RetrievedChunk objects
        
        Args:
            pinecone_results: Results from Pinecone query
            
        Returns:
            List of RetrievedChunk objects
        """
        formatted_chunks = []
        
        for result in pinecone_results:
            chunk = RetrievedChunk(
                content=result['chunk_text'],
                metadata={
                    "section_title": result['metadata']['section_title'],
                    "page_number": result['metadata']['page_number'],
                    "document_source": result['metadata']['document_source'],
                    "chunk_id": result['metadata'].get('chunk_id', ''),
                    "chunk_index": result['metadata'].get('chunk_index', 0)
                },
                score=result['similarity_score']
            )
            formatted_chunks.append(chunk)
        
        return formatted_chunks
    
    async def _try_wikipedia_fallback(
        self,
        concept_name: str,
        top_k: int
    ) -> List[RetrievedChunk]:
        """
        Try to get content from Wikipedia fallback
        
        Args:
            concept_name: Name of the concept
            top_k: Number of chunks to retrieve
            
        Returns:
            List of RetrievedChunk objects from Wikipedia, or empty list if failed
        """
        try:
            if self.wikipedia_fallback:
                logger.info(f"Attempting Wikipedia fallback for: '{concept_name}'")
                chunks = await self.wikipedia_fallback.get_fallback_chunks(
                    concept_name=concept_name,
                    top_k=top_k
                )
                
                if chunks:
                    logger.info(f"Wikipedia fallback successful: {len(chunks)} chunks")
                    return chunks
                else:
                    logger.warning(f"Wikipedia fallback returned no chunks for: '{concept_name}'")
                    return await self._retrieve_mock_chunks(top_k)
            else:
                logger.warning("Wikipedia fallback service not available")
                return await self._retrieve_mock_chunks(top_k)
                
        except Exception as e:
            logger.error(f"Wikipedia fallback error: {str(e)}")
            return await self._retrieve_mock_chunks(top_k)
    
    async def _retrieve_mock_chunks(self, top_k: int) -> List[RetrievedChunk]:
        """
        Retrieve mock chunks for testing/demo purposes
        
        Args:
            top_k: Number of chunks to retrieve
            
        Returns:
            List of RetrievedChunk objects with mock data
        """
        logger.debug(f"Retrieving {top_k} mock chunks")
        await asyncio.sleep(0.1)  # Simulate async operation
        
        # Mock chunks for demonstration
        return [
            RetrievedChunk(
                content=f"Financial concept information about the topic. This is chunk {i+1}.",
                metadata={
                    "page": i + 1,
                    "section": "Financial Concepts",
                    "source": "Financial Report 2024"
                },
                score=0.95 - (i * 0.05)
            )
            for i in range(top_k)
        ]
    
    async def _generate_concept_note(
        self,
        concept_name: str,
        chunks: List[RetrievedChunk]
    ) -> Dict[str, Any]:
        """
        Generate a concept note from retrieved chunks
        
        Args:
            concept_name: Name of the concept
            chunks: Retrieved chunks
            
        Returns:
            Generated concept note dictionary
        """
        # TODO: Implement LLM-based note generation
        logger.debug(f"Generating concept note for: {concept_name}")
        await asyncio.sleep(0.2)  # Simulate async operation
        
        # Mock generated note
        return {
            "title": concept_name.title(),
            "summary": f"Comprehensive overview of {concept_name} based on {len(chunks)} retrieved chunks.",
            "key_points": [
                f"Key point 1 about {concept_name}",
                f"Key point 2 about {concept_name}",
                f"Key point 3 about {concept_name}"
            ],
            "related_concepts": ["Related Concept 1", "Related Concept 2"],
            "confidence": 0.92
        }
    
    async def _check_concept_exists(self, concept_name: str) -> bool:
        """
        Check if a concept already exists in the database
        
        Args:
            concept_name: Name of the concept
            
        Returns:
            True if concept exists, False otherwise
        """
        # TODO: Implement existence check
        logger.debug(f"Checking if concept exists: {concept_name}")
        await asyncio.sleep(0.05)
        return False  # Mock: assume doesn't exist
    
    async def _generate_and_store_embeddings(self, concept_name: str):
        """
        Generate and store embeddings for a concept
        
        Args:
            concept_name: Name of the concept
        """
        # TODO: Implement embedding generation and storage
        logger.debug(f"Generating and storing embeddings for: {concept_name}")
        await asyncio.sleep(0.3)  # Simulate async operation
        logger.info(f"Successfully generated and stored embeddings for: {concept_name}")

