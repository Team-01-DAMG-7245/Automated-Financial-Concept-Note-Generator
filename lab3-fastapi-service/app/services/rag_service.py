"""
RAG Service for querying and seeding financial concepts
"""
from datetime import datetime, timedelta
import os
import logging
from typing import List, Dict, Any
import asyncio
from app.models.schemas import QueryResponse, SeedResponse, RetrievedChunk, ConceptNote
from app.services.pinecone_service import PineconeService, PineconeQueryError
from app.services.local_vector_service import LocalVectorService
from app.services.wikipedia_fallback import WikipediaFallbackService
from app.core.db import SessionLocal, Base, engine
from app.services.generator import generate_concept_note
from app.services.repo import get_cached_concept, upsert_concept_note

logger = logging.getLogger(__name__)


# Ensure DB tables exist (safe to call at import time)
Base.metadata.create_all(bind=engine)

# Cache freshness window
MAX_CACHE_AGE_HOURS = int(os.getenv("MAX_CACHE_AGE_HOURS", "720"))

def _is_stale(dt: datetime) -> bool:
    return (datetime.utcnow() - dt) > timedelta(hours=MAX_CACHE_AGE_HOURS)


class RAGService:
    """
    Service for Retrieval-Augmented Generation operations
    """
    
    def __init__(self):
        """
        Initialize RAG service with vector store and LLM
        """
        self.pinecone_service: PineconeService = None
        self.local_vector_service: LocalVectorService = None
        self.wikipedia_fallback: WikipediaFallbackService = None
        self.llm = None
        self._initialize_components()
    
    def _initialize_components(self):
        """
        Initialize vector store and LLM components
        """
        try:
            # Initialize Local Vector Service (Primary - uses lab1 data)
            self.local_vector_service = LocalVectorService()
            logger.info("Local vector service initialized with lab1 data")
            
            # Initialize Pinecone service (Secondary - for cloud deployment)
            self.pinecone_service = PineconeService()
            
            # Test Pinecone connection
            if self.pinecone_service.test_connection():
                logger.info("Pinecone connection verified")
            else:
                logger.warning("Pinecone connection test failed, will use local vector service")
            
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
    
    async def query_concept(self, concept_name: str, top_k: int = 5) -> QueryResponse:
        logger.info(f"Querying concept: {concept_name} with top_k={top_k}")

        # --- 0) CACHE LOOKUP ---
        with SessionLocal() as db:
            row = get_cached_concept(db, concept_name.strip())
            if row and not _is_stale(row.generated_at):
                logger.info(f"Cache hit for concept: {concept_name}")
                cached_note = ConceptNote(
                    concept=row.concept,
                    definition=row.definition,
                    intuition=row.intuition,
                    formulae=row.formulae,
                    step_by_step=row.step_by_step,
                    pitfalls=row.pitfalls,
                    examples=row.examples,
                    citations=row.citations,
                    used_fallback=row.used_fallback,
                    generated_at=row.generated_at,
                )
                return QueryResponse(
                    concept_name=concept_name,
                    retrieved_chunks=[],
                    source="cache",
                    generated_note=cached_note.model_dump(),
                )

        # --- 1) RETRIEVE (Primary: Local Vector Service, Secondary: Pinecone, Fallback: Wikipedia) ---
        chunks = []
        source = "No results"
        
        try:
            # PRIMARY: Try local vector service first (lab1 data)
            if self.local_vector_service and self.local_vector_service.chunks_data:
                logger.info(f"Querying local vector service for: '{concept_name}'")
                
                # Generate query embedding using OpenAI
                query_embedding = await self._generate_query_embedding(concept_name)
                if query_embedding:
                    local_results = self.local_vector_service.query_chunks(
                        query_embedding=query_embedding,
                        top_k=top_k,
                        threshold=0.01  # Very low threshold for testing
                    )
                    
                    if local_results:
                        logger.info(f"Retrieved {len(local_results)} chunks from local vector service")
                        chunks = local_results
                        source = "fintbx_pdf (Local Vector Service)"
                    else:
                        logger.warning("No results from local vector service, trying Pinecone")
            
            # SECONDARY: Try Pinecone if local service has no results
            if not chunks and self.pinecone_service and self.pinecone_service.index:
                logger.info("Attempting Pinecone query as secondary source")
                pinecone_results = await self.pinecone_service.query_similar_chunks(
                    concept_query=concept_name,
                    top_k=top_k
                )
                if pinecone_results:
                    logger.info(f"Retrieved {len(pinecone_results)} chunks from Pinecone")
                    chunks = self._format_pinecone_results(pinecone_results)
                    source = "fintbx_pdf (Pinecone Vector DB)"
            
            # FALLBACK: Try Wikipedia if both vector services have no results
            if not chunks:
                logger.warning("No results from vector services, attempting Wikipedia fallback")
                chunks = await self._try_wikipedia_fallback(concept_name, top_k)
                source = "wikipedia (Fallback)" if chunks else "Mock Data (No results)"
                
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}, attempting Wikipedia fallback")
            chunks = await self._try_wikipedia_fallback(concept_name, top_k)
            source = "wikipedia (Fallback)" if chunks else "Mock Data (Retrieval error)"

        # --- 2) GENERATE (Instructor) ---
        generated_note = await self._generate_concept_note(concept_name=concept_name, chunks=chunks)

        # --- 3) UPSERT CACHE ---
        try:
            # convert dict back to ConceptNote for repo (pydantic will validate)
            note_obj = ConceptNote(**generated_note)
            with SessionLocal() as db:
                upsert_concept_note(db, note_obj)
                db.commit()
        except Exception as e:
            logger.warning(f"Cache upsert failed for '{concept_name}': {e}")

        # --- 4) RESPONSE ---
        return QueryResponse(
            concept_name=concept_name,
            retrieved_chunks=chunks,
            source=source,
            generated_note=generated_note
        )

    
    async def seed_concept(self, concept_name: str, force_refresh: bool = False) -> SeedResponse:
        logger.info(f"Seeding concept: {concept_name}, force_refresh={force_refresh}")

        # respect existing cache unless forced
        with SessionLocal() as db:
            row = get_cached_concept(db, concept_name.strip())
            if row and not force_refresh and not _is_stale(row.generated_at):
                return SeedResponse(
                    success=True,
                    message=f"Concept '{concept_name}' already cached; skipped. Use force_refresh=true to update.",
                    concept_name=concept_name
                )

        # retrieve
        chunks: List[RetrievedChunk] = []
        try:
            if self.pinecone_service and self.pinecone_service.index:
                pine = await self.pinecone_service.query_similar_chunks(concept_query=concept_name, top_k=5)
                if pine:
                    chunks = self._format_pinecone_results(pine)
        except Exception as e:
            logger.warning(f"Pinecone error during seed: {e}")

        if not chunks:
            chunks = await self._try_wikipedia_fallback(concept_name, top_k=5)
            if not chunks:
                return SeedResponse(success=False, message="No sources found", concept_name=concept_name)

        # generate + upsert
        note = await self._generate_concept_note(concept_name, chunks)
        try:
            with SessionLocal() as db:
                upsert_concept_note(db, ConceptNote(**note))
                db.commit()
        except Exception as e:
            logger.error(f"Failed to upsert cache during seed: {e}")
            return SeedResponse(success=False, message=f"Seed failed: {e}", concept_name=concept_name)

        return SeedResponse(success=True, message="Concept seeded successfully", concept_name=concept_name)

    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query using OpenAI
        
        Args:
            query: Query string
            
        Returns:
            Query embedding vector
        """
        try:
            if self.pinecone_service and self.pinecone_service.openai_client:
                logger.debug(f"Generating OpenAI embedding for query: {query}")
                
                response = self.pinecone_service.openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=query
                )
                
                embedding = response.data[0].embedding
                logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.warning("OpenAI client not available, using mock embedding")
                # Use a more realistic mock embedding that might match some content
                return [0.01] * 3072  # Smaller values for better similarity
                
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return [0.01] * 3072  # Fallback mock embedding
    
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
            md = result.get("metadata", {}) or {}
            # normalize names expected by the generator/citations
            metadata = {
                "source_type": "pdf",
                "title": md.get("section_title"),
                "page": md.get("page_number"),
                "url": md.get("document_source"),   # if you have a URL, put it here
                "document_source": md.get("document_source"),
                "section_title": md.get("section_title"),
                "page_number": md.get("page_number"),
                "chunk_id": md.get("chunk_id", ""),
                "chunk_index": md.get("chunk_index", 0),
            }
            formatted_chunks.append(
                RetrievedChunk(
                    content=result.get("chunk_text", ""),
                    metadata=metadata,
                    score=result.get("similarity_score"),
                )
        )
        
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
                chunks = await self.wikipedia_fallback.get_fallback_chunks(concept_name=concept_name, top_k=top_k)
                if chunks:
                    # tag all as wikipedia sources
                    for ch in chunks:
                        md = ch.metadata or {}
                        md["source_type"] = "wikipedia"
                        ch.metadata = md
                    logger.info(f"Wikipedia fallback successful: {len(chunks)} chunks")
                    return chunks
                logger.warning(f"Wikipedia fallback returned no chunks for: '{concept_name}'")
                return await self._retrieve_mock_chunks(top_k)
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
        Generate a structured concept note using Instructor/OpenAI.
        Returns a plain dict to match your QueryResponse schema.
        """
        logger.debug(f"Generating concept note for: {concept_name}")
        # call the structured generator (sync) in a thread to avoid blocking loop
        note: ConceptNote = await asyncio.to_thread(generate_concept_note, concept_name, chunks)
        return note.model_dump()

    
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

