"""
Embeddings Module for AURELIA
Uses OpenAI's text-embedding-3-large model with batching, caching, and cost tracking
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
import hashlib

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI imports
from openai import OpenAI, RateLimitError, APIError, APIConnectionError, APITimeoutError

# Progress bar
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingStats:
    """Statistics for embedding operations"""
    total_chunks: int = 0
    embedded_chunks: int = 0
    cached_chunks: int = 0
    failed_chunks: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_time: float = 0.0
    api_calls: int = 0
    retries: int = 0
    
    def to_dict(self):
        return {
            'total_chunks': self.total_chunks,
            'embedded_chunks': self.embedded_chunks,
            'cached_chunks': self.cached_chunks,
            'failed_chunks': self.failed_chunks,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'total_time': self.total_time,
            'api_calls': self.api_calls,
            'retries': self.retries
        }


class Embedder:
    """
    Embedding service using OpenAI's text-embedding-3-large model
    """
    
    # Pricing for text-embedding-3-large (as of 2024)
    PRICE_PER_TOKEN = 0.00013 / 1000  # $0.00013 per 1K tokens
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "text-embedding-3-large",
                 batch_size: int = 100,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 cache_dir: str = "outputs/embeddings_cache",
                 dimension: int = 3072):
        """
        Initialize the embedder
        
        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            model: Embedding model to use
            batch_size: Number of chunks to process per API call
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
            cache_dir: Directory to store cached embeddings
            dimension: Embedding dimension (default 3072 for text-embedding-3-large)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dimension = dimension
        
        # Setup cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'embeddings_cache.json'
        self.cache = self._load_cache()
        
        # Statistics
        self.stats = EmbeddingStats()
        
        logger.info(f"Initialized Embedder with model={model}, batch_size={batch_size}, dimension={dimension}")
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load embeddings cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached embeddings from {self.cache_file}")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save embeddings cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} cached embeddings to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_cache_key(self, chunk: Chunk) -> str:
        """Generate cache key for a chunk"""
        # Use content + metadata to generate unique key
        content = chunk.content
        metadata_str = json.dumps(chunk.metadata, sort_keys=True)
        key_string = f"{content}:{metadata_str}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cached(self, chunk: Chunk) -> bool:
        """Check if chunk is cached"""
        cache_key = self._get_cache_key(chunk)
        return cache_key in self.cache
    
    def _get_cached_embedding(self, chunk: Chunk) -> Optional[List[float]]:
        """Get cached embedding for a chunk"""
        cache_key = self._get_cache_key(chunk)
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            # Verify model version matches
            if cached_data.get('model') == self.model:
                return cached_data.get('embedding')
        
        return None
    
    def _cache_embedding(self, chunk: Chunk, embedding: List[float], tokens: int):
        """Cache an embedding"""
        cache_key = self._get_cache_key(chunk)
        self.cache[cache_key] = {
            'embedding': embedding,
            'model': self.model,
            'dimension': self.dimension,
            'timestamp': datetime.now().isoformat(),
            'tokens': tokens,
            'metadata': chunk.metadata
        }
    
    def _calculate_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost for embedding tokens"""
        return tokens * self.PRICE_PER_TOKEN
    
    def _call_api_with_retry(self, texts: List[str]) -> Tuple[List[List[float]], int]:
        """
        Call OpenAI API with retry logic and exponential backoff
        
        Returns:
            Tuple of (embeddings, tokens_used)
        """
        retries = 0
        delay = self.retry_delay
        
        while retries <= self.max_retries:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimension
                )
                
                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                tokens_used = response.usage.total_tokens
                
                self.stats.api_calls += 1
                return embeddings, tokens_used
                
            except RateLimitError as e:
                retries += 1
                self.stats.retries += 1
                
                if retries > self.max_retries:
                    logger.error(f"Rate limit exceeded after {self.max_retries} retries")
                    raise
                
                logger.warning(f"Rate limit hit. Retrying in {delay}s (attempt {retries}/{self.max_retries})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
                
            except (APIConnectionError, APITimeoutError) as e:
                retries += 1
                self.stats.retries += 1
                
                if retries > self.max_retries:
                    logger.error(f"Connection error after {self.max_retries} retries: {e}")
                    raise
                
                logger.warning(f"Connection error. Retrying in {delay}s (attempt {retries}/{self.max_retries})")
                time.sleep(delay)
                delay *= 2
                
            except APIError as e:
                logger.error(f"API error: {e}")
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        raise Exception("Failed to get embeddings after all retries")
    
    def embed_chunks(self, chunks: List[Chunk], show_progress: bool = True) -> List[Chunk]:
        """
        Embed a list of chunks
        
        Args:
            chunks: List of Chunk objects to embed
            show_progress: Whether to show progress bar
            
        Returns:
            List of Chunk objects with embeddings
        """
        start_time = time.time()
        self.stats.total_chunks = len(chunks)
        
        logger.info(f"Starting embedding for {len(chunks)} chunks")
        
        # Check cache first
        chunks_to_embed = []
        cached_count = 0
        
        for chunk in chunks:
            if self._is_cached(chunk):
                cached_embedding = self._get_cached_embedding(chunk)
                if cached_embedding:
                    chunk.embeddings = cached_embedding
                    cached_count += 1
                    self.stats.cached_chunks += 1
                else:
                    chunks_to_embed.append(chunk)
            else:
                chunks_to_embed.append(chunk)
        
        if cached_count > 0:
            logger.info(f"Found {cached_count} cached embeddings")
        
        if not chunks_to_embed:
            logger.info("All chunks already cached!")
            self.stats.total_time = time.time() - start_time
            return chunks
        
        # Process in batches
        total_batches = (len(chunks_to_embed) + self.batch_size - 1) // self.batch_size
        
        progress_bar = tqdm(
            total=len(chunks_to_embed),
            desc="Embedding chunks",
            unit="chunk",
            disable=not show_progress
        )
        
        for i in range(0, len(chunks_to_embed), self.batch_size):
            batch = chunks_to_embed[i:i + self.batch_size]
            batch_texts = [chunk.content for chunk in batch]
            
            try:
                # Get embeddings
                embeddings, tokens_used = self._call_api_with_retry(batch_texts)
                
                # Update chunks with embeddings
                for chunk, embedding in zip(batch, embeddings):
                    chunk.embeddings = embedding
                    
                    # Cache the embedding
                    chunk_tokens = self._calculate_tokens(chunk.content)
                    self._cache_embedding(chunk, embedding, chunk_tokens)
                    
                    self.stats.embedded_chunks += 1
                    self.stats.total_tokens += chunk_tokens
                
                progress_bar.update(len(batch))
                
                # Log progress
                if (i // self.batch_size + 1) % 10 == 0:
                    logger.info(f"Processed {i + len(batch)}/{len(chunks_to_embed)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing batch {i // self.batch_size + 1}: {e}")
                self.stats.failed_chunks += len(batch)
                # Continue with next batch
                continue
        
        progress_bar.close()
        
        # Calculate costs
        self.stats.total_cost = self._estimate_cost(self.stats.total_tokens)
        self.stats.total_time = time.time() - start_time
        
        # Save cache
        self._save_cache()
        
        # Log summary
        logger.info("=" * 80)
        logger.info("EMBEDDING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total chunks: {self.stats.total_chunks}")
        logger.info(f"Embedded: {self.stats.embedded_chunks}")
        logger.info(f"Cached: {self.stats.cached_chunks}")
        logger.info(f"Failed: {self.stats.failed_chunks}")
        logger.info(f"Total tokens: {self.stats.total_tokens:,}")
        logger.info(f"Estimated cost: ${self.stats.total_cost:.4f}")
        logger.info(f"Total time: {self.stats.total_time:.2f}s")
        logger.info(f"API calls: {self.stats.api_calls}")
        logger.info(f"Retries: {self.stats.retries}")
        logger.info("=" * 80)
        
        return chunks
    
    def estimate_cost(self, chunks: List[Chunk]) -> float:
        """
        Estimate the cost of embedding chunks
        
        Args:
            chunks: List of Chunk objects
            
        Returns:
            Estimated cost in USD
        """
        total_tokens = sum(self._calculate_tokens(chunk.content) for chunk in chunks)
        return self._estimate_cost(total_tokens)
    
    def validate_embeddings(self, chunks: List[Chunk]) -> bool:
        """
        Validate that all chunks have embeddings
        
        Args:
            chunks: List of Chunk objects
            
        Returns:
            True if all chunks have valid embeddings
        """
        valid_count = 0
        invalid_count = 0
        
        for i, chunk in enumerate(chunks):
            if chunk.embeddings is None:
                logger.warning(f"Chunk {i} has no embedding")
                invalid_count += 1
            elif not isinstance(chunk.embeddings, list):
                logger.warning(f"Chunk {i} has invalid embedding type: {type(chunk.embeddings)}")
                invalid_count += 1
            elif len(chunk.embeddings) != self.dimension:
                logger.warning(f"Chunk {i} has wrong embedding dimension: {len(chunk.embeddings)} != {self.dimension}")
                invalid_count += 1
            else:
                valid_count += 1
        
        logger.info(f"Validation: {valid_count} valid, {invalid_count} invalid")
        
        return invalid_count == 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics"""
        return self.stats.to_dict()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = EmbeddingStats()
        logger.info("Statistics reset")


def test_embedder():
    """Test the embedder with sample chunks"""
    
    # Create sample chunks
    sample_chunks = [
        Chunk(
            content="The Financial Toolbox provides comprehensive functions for financial analysis.",
            metadata={'page': 1, 'section': 'Introduction'},
            embeddings=None
        ),
        Chunk(
            content="Portfolio optimization involves selecting assets to maximize returns while minimizing risk.",
            metadata={'page': 2, 'section': 'Portfolio Theory'},
            embeddings=None
        ),
        Chunk(
            content="The Sharpe Ratio measures risk-adjusted return: SR = (Rp - Rf) / σp",
            metadata={'page': 3, 'section': 'Risk Metrics'},
            embeddings=None
        )
    ]
    
    # Initialize embedder
    embedder = Embedder(
        batch_size=2,
        cache_dir="outputs/test_embeddings_cache"
    )
    
    print("\n" + "=" * 80)
    print("EMBEDDER TEST")
    print("=" * 80 + "\n")
    
    # Estimate cost
    cost = embedder.estimate_cost(sample_chunks)
    print(f"Estimated cost for {len(sample_chunks)} chunks: ${cost:.4f}")
    print()
    
    # Embed chunks
    print("Embedding chunks...")
    embedded_chunks = embedder.embed_chunks(sample_chunks, show_progress=True)
    print()
    
    # Validate embeddings
    is_valid = embedder.validate_embeddings(embedded_chunks)
    print(f"Validation: {'PASSED' if is_valid else 'FAILED'}")
    print()
    
    # Show stats
    print("Statistics:")
    stats = embedder.get_stats()
    print(json.dumps(stats, indent=2))
    print()
    
    # Test caching (run again)
    print("Testing cache (second run should use cache)...")
    embedded_chunks_2 = embedder.embed_chunks(sample_chunks, show_progress=True)
    print()
    
    # Show stats after caching
    print("Statistics after caching:")
    stats_2 = embedder.get_stats()
    print(json.dumps(stats_2, indent=2))
    print()
    
    print("=" * 80)
    print("[OK] Embedder test complete!")
    print("=" * 80)


if __name__ == '__main__':
    test_embedder()

