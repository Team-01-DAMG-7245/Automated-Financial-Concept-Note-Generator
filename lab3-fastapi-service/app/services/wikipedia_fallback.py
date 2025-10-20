"""
Wikipedia Fallback Service for AURELIA RAG
Provides fallback content retrieval when vector store returns no results
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
import wikipediaapi
from app.models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class WikipediaFallbackError(Exception):
    """Custom exception for Wikipedia fallback errors"""
    pass


class WikipediaFallbackService:
    """
    Service for retrieving Wikipedia content as fallback when vector store has no results
    """
    
    def __init__(self):
        """
        Initialize Wikipedia fallback service
        """
        self.wiki = wikipediaapi.Wikipedia(
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='AURELIA-RAG-Service/1.0 (https://github.com/your-repo)'
        )
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        self.chunk_size = 500  # Characters per chunk
        self.chunk_overlap = 50  # Overlap between chunks
        
        logger.info("Wikipedia fallback service initialized")
    
    def _rate_limit(self) -> None:
        """
        Implement rate limiting for Wikipedia API calls
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def fetch_wikipedia_content(
        self,
        concept_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch Wikipedia content for a given concept
        
        Args:
            concept_name: Name of the concept to search for
            
        Returns:
            Dictionary with Wikipedia content and metadata, or None if not found
            
        Raises:
            WikipediaFallbackError: If Wikipedia retrieval fails
        """
        try:
            logger.info(f"Fetching Wikipedia content for: '{concept_name}'")
            
            # Rate limiting
            self._rate_limit()
            
            # Search for the page
            page = self.wiki.page(concept_name)
            
            if not page.exists():
                logger.warning(f"Wikipedia page not found for: '{concept_name}'")
                return None
            
            # Extract content
            content = page.text
            
            if not content or len(content) < 100:
                logger.warning(f"Wikipedia content too short for: '{concept_name}'")
                return None
            
            # Clean and parse content
            cleaned_content = self._clean_content(content)
            
            # Chunk the content
            chunks = self._chunk_content(cleaned_content)
            
            logger.info(
                f"Successfully fetched Wikipedia content for '{concept_name}': "
                f"{len(chunks)} chunks, {len(content)} characters"
            )
            
            return {
                'title': page.title,
                'url': page.fullurl,
                'content': cleaned_content,
                'chunks': chunks,
                'total_chunks': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia content for '{concept_name}': {str(e)}")
            raise WikipediaFallbackError(f"Wikipedia retrieval failed: {str(e)}")
    
    def _clean_content(self, content: str) -> str:
        """
        Clean Wikipedia content by removing citations and formatting
        
        Args:
            content: Raw Wikipedia content
            
        Returns:
            Cleaned content
        """
        # Remove citations like [1], [2], etc.
        content = re.sub(r'\[\d+\]', '', content)
        
        # Remove multiple citations like [1][2][3]
        content = re.sub(r'\[\d+\]+', '', content)
        
        # Remove reference sections
        content = re.sub(r'== References ==.*', '', content, flags=re.DOTALL)
        content = re.sub(r'== See also ==.*', '', content, flags=re.DOTALL)
        content = re.sub(r'== External links ==.*', '', content, flags=re.DOTALL)
        
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Remove section headers (keep the content)
        content = re.sub(r'^== .+ ==$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^=== .+ ===$', '', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _chunk_content(self, content: str) -> List[str]:
        """
        Chunk Wikipedia content into manageable pieces
        
        Args:
            content: Cleaned Wikipedia content
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + " " + paragraph
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If we have very few chunks, try to split large ones
        if len(chunks) < 3 and content:
            # Split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                if not sentence:
                    continue
                
                if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap_text + " " + sentence
                else:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        return chunks
    
    async def get_fallback_chunks(
        self,
        concept_name: str,
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """
        Get Wikipedia chunks as fallback for a concept
        
        Args:
            concept_name: Name of the concept
            top_k: Number of chunks to return
            
        Returns:
            List of RetrievedChunk objects from Wikipedia
        """
        try:
            logger.info(f"Attempting Wikipedia fallback for: '{concept_name}'")
            
            # Fetch Wikipedia content
            wiki_data = await self.fetch_wikipedia_content(concept_name)
            
            if not wiki_data:
                logger.warning(f"No Wikipedia content found for: '{concept_name}'")
                return []
            
            # Convert to RetrievedChunk objects
            chunks = []
            for i, chunk_text in enumerate(wiki_data['chunks'][:top_k]):
                chunk = RetrievedChunk(
                    content=chunk_text,
                    metadata={
                        'source': 'Wikipedia',
                        'title': wiki_data['title'],
                        'url': wiki_data['url'],
                        'chunk_index': i,
                        'total_chunks': wiki_data['total_chunks']
                    },
                    score=0.8  # Default score for Wikipedia content
                )
                chunks.append(chunk)
            
            logger.info(
                f"Wikipedia fallback successful for '{concept_name}': "
                f"returned {len(chunks)} chunks"
            )
            
            return chunks
            
        except WikipediaFallbackError as e:
            logger.error(f"Wikipedia fallback error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Wikipedia fallback: {str(e)}")
            return []

