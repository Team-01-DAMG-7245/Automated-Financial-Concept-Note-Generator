"""
Pinecone Storage Module for AURELIA
Stores and queries embedded chunks using Pinecone vector database
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Pinecone imports
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeException

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk
from embeddings.embedder import Embedder

# Progress bar
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PineconeStore:
    """
    Pinecone vector database storage for embedded chunks
    """
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 index_name: str = "fintbx-embeddings",
                 dimension: int = 3072,
                 metric: str = "cosine",
                 cloud: str = "aws",
                 region: str = "us-east-1",
                 batch_size: int = 100):
        """
        Initialize Pinecone store
        
        Args:
            api_key: Pinecone API key (or use PINECONE_API_KEY env var)
            index_name: Name of the index
            dimension: Vector dimension (3072 for text-embedding-3-large)
            metric: Distance metric (cosine, euclidean, dotproduct)
            cloud: Cloud provider (aws, gcp, azure)
            region: Cloud region
            batch_size: Batch size for upserts
        """
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        if not self.api_key:
            raise ValueError("Pinecone API key not provided. Set PINECONE_API_KEY environment variable or pass api_key parameter.")
        
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.batch_size = batch_size
        
        # Initialize Pinecone client
        try:
            self.pc = Pinecone(api_key=self.api_key)
            logger.info(f"Initialized Pinecone client")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise
        
        # Initialize embedder for query embeddings
        self.embedder = Embedder(
            model="text-embedding-3-large",
            dimension=dimension
        )
        
        # Statistics
        self.stats = {
            'total_vectors': 0,
            'upserted_vectors': 0,
            'failed_vectors': 0,
            'total_time': 0.0,
            'queries': 0
        }
        
        logger.info(f"Initialized PineconeStore with index={index_name}, dimension={dimension}, metric={metric}")
    
    def create_index(self, force: bool = False):
        """
        Create Pinecone index
        
        Args:
            force: If True, delete existing index and create new one
        """
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_exists = any(index.name == self.index_name for index in existing_indexes)
            
            if index_exists:
                if force:
                    logger.info(f"Deleting existing index: {self.index_name}")
                    self.pc.delete_index(self.index_name)
                    time.sleep(5)  # Wait for deletion
                else:
                    logger.info(f"Index {self.index_name} already exists")
                    self.index = self.pc.Index(self.index_name)
                    return
            
            # Create new index
            logger.info(f"Creating index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(
                    cloud=self.cloud,
                    region=self.region
                )
            )
            
            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            time.sleep(10)
            
            # Get index
            self.index = self.pc.Index(self.index_name)
            
            logger.info(f"[OK] Index {self.index_name} created successfully")
            
        except PineconeException as e:
            logger.error(f"Pinecone error creating index: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating index: {e}")
            raise
    
    def connect_index(self):
        """Connect to existing index"""
        try:
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to index: {self.index_name}")
            
            # Get index stats
            stats = self.index.describe_index_stats()
            logger.info(f"Index stats: {stats}")
            
        except Exception as e:
            logger.error(f"Failed to connect to index: {e}")
            raise
    
    def upsert_chunks(self, chunks: List[Chunk], namespace: Optional[str] = None, show_progress: bool = True):
        """
        Upsert chunks to Pinecone
        
        Args:
            chunks: List of Chunk objects with embeddings
            namespace: Optional namespace (e.g., topic/section)
            show_progress: Show progress bar
            
        Returns:
            Number of vectors upserted
        """
        start_time = time.time()
        self.stats['total_vectors'] = len(chunks)
        
        logger.info(f"Starting upsert for {len(chunks)} chunks to namespace: {namespace or 'default'}")
        
        # Prepare vectors
        vectors = []
        for i, chunk in enumerate(chunks):
            if chunk.embeddings is None:
                logger.warning(f"Chunk {i} has no embeddings, skipping")
                self.stats['failed_vectors'] += 1
                continue
            
            # Generate unique ID
            chunk_id = chunk.metadata.get('chunk_id', f"chunk_{i}")
            
            # Prepare metadata
            metadata = {
                'content': chunk.content,
                'section_title': chunk.metadata.get('section_title', ''),
                'page_range': chunk.metadata.get('page_range', ''),
                'chunk_type': chunk.metadata.get('chunk_type', 'text'),
                'routing_strategy': chunk.metadata.get('routing_strategy', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add all metadata (convert nested structures to JSON strings)
            for key, value in chunk.metadata.items():
                if key not in ['chunk_id', 'embeddings']:
                    # Pinecone only accepts string, number, boolean, or list of strings
                    if isinstance(value, (dict, list)):
                        # Convert nested structures to JSON strings
                        metadata[key] = json.dumps(value)
                    elif isinstance(value, str) and len(value) > 1000:
                        # Truncate very long strings
                        metadata[key] = value[:1000]
                    else:
                        metadata[key] = value
            
            vectors.append({
                'id': chunk_id,
                'values': chunk.embeddings,
                'metadata': metadata
            })
        
        # Batch upsert
        total_batches = (len(vectors) + self.batch_size - 1) // self.batch_size
        
        progress_bar = tqdm(
            total=len(vectors),
            desc=f"Upserting to {namespace or 'default'}",
            unit="vector",
            disable=not show_progress
        )
        
        for i in range(0, len(vectors), self.batch_size):
            batch = vectors[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            try:
                # Upsert batch
                if namespace:
                    self.index.upsert(vectors=batch, namespace=namespace)
                else:
                    self.index.upsert(vectors=batch)
                
                self.stats['upserted_vectors'] += len(batch)
                progress_bar.update(len(batch))
                
                # Log progress
                if batch_num % 10 == 0:
                    logger.info(f"Upserted {i + len(batch)}/{len(vectors)} vectors")
                
            except PineconeException as e:
                logger.error(f"Pinecone error upserting batch {batch_num}: {e}")
                self.stats['failed_vectors'] += len(batch)
                # Continue with next batch
                continue
            except Exception as e:
                logger.error(f"Unexpected error upserting batch {batch_num}: {e}")
                self.stats['failed_vectors'] += len(batch)
                continue
        
        progress_bar.close()
        
        self.stats['total_time'] = time.time() - start_time
        
        # Log summary
        logger.info("=" * 80)
        logger.info("UPSERT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total vectors: {self.stats['total_vectors']}")
        logger.info(f"Upserted: {self.stats['upserted_vectors']}")
        logger.info(f"Failed: {self.stats['failed_vectors']}")
        logger.info(f"Total time: {self.stats['total_time']:.2f}s")
        logger.info(f"Vectors/sec: {self.stats['upserted_vectors'] / self.stats['total_time']:.2f}")
        logger.info("=" * 80)
        
        return self.stats['upserted_vectors']
    
    def query_by_text(self, query: str, top_k: int = 5, namespace: Optional[str] = None, 
                      include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Query Pinecone by text (embeds query first)
        
        Args:
            query: Query text
            top_k: Number of results to return
            namespace: Optional namespace
            include_metadata: Include metadata in results
            
        Returns:
            List of query results
        """
        start_time = time.time()
        self.stats['queries'] += 1
        
        logger.info(f"Querying by text: '{query[:50]}...' (top_k={top_k})")
        
        # Embed query
        query_chunk = Chunk(content=query, metadata={})
        embedded_chunks = self.embedder.embed_chunks([query_chunk], show_progress=False)
        query_vector = embedded_chunks[0].embeddings
        
        # Query Pinecone
        try:
            if namespace:
                results = self.index.query(
                    vector=query_vector,
                    top_k=top_k,
                    namespace=namespace,
                    include_metadata=include_metadata
                )
            else:
                results = self.index.query(
                    vector=query_vector,
                    top_k=top_k,
                    include_metadata=include_metadata
                )
            
            query_time = time.time() - start_time
            
            logger.info(f"Query completed in {query_time:.3f}s, found {len(results.matches)} results")
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata if include_metadata else {}
                })
            
            return formatted_results
            
        except PineconeException as e:
            logger.error(f"Pinecone error querying: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error querying: {e}")
            raise
    
    def query_by_vector(self, vector: List[float], top_k: int = 5, namespace: Optional[str] = None,
                        include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Query Pinecone by vector
        
        Args:
            vector: Query vector
            top_k: Number of results to return
            namespace: Optional namespace
            include_metadata: Include metadata in results
            
        Returns:
            List of query results
        """
        start_time = time.time()
        self.stats['queries'] += 1
        
        logger.info(f"Querying by vector (top_k={top_k})")
        
        # Query Pinecone
        try:
            if namespace:
                results = self.index.query(
                    vector=vector,
                    top_k=top_k,
                    namespace=namespace,
                    include_metadata=include_metadata
                )
            else:
                results = self.index.query(
                    vector=vector,
                    top_k=top_k,
                    include_metadata=include_metadata
                )
            
            query_time = time.time() - start_time
            
            logger.info(f"Query completed in {query_time:.3f}s, found {len(results.matches)} results")
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata if include_metadata else {}
                })
            
            return formatted_results
            
        except PineconeException as e:
            logger.error(f"Pinecone error querying: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error querying: {e}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'namespaces': dict(stats.namespaces) if stats.namespaces else {},
                'dimension': stats.dimension
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
    
    def delete_index(self):
        """Delete the index"""
        try:
            logger.warning(f"Deleting index: {self.index_name}")
            self.pc.delete_index(self.index_name)
            logger.info(f"Index {self.index_name} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_vectors': 0,
            'upserted_vectors': 0,
            'failed_vectors': 0,
            'total_time': 0.0,
            'queries': 0
        }
        logger.info("Statistics reset")


def test_pinecone_store():
    """Test the Pinecone store"""
    
    # Create sample chunks
    sample_chunks = [
        Chunk(
            content="The Financial Toolbox provides comprehensive functions for financial analysis.",
            metadata={'page': 1, 'section': 'Introduction', 'chunk_id': 'chunk_1'},
            embeddings=[0.1] * 3072  # Dummy embeddings
        ),
        Chunk(
            content="Portfolio optimization involves selecting assets to maximize returns while minimizing risk.",
            metadata={'page': 2, 'section': 'Portfolio Theory', 'chunk_id': 'chunk_2'},
            embeddings=[0.2] * 3072
        ),
        Chunk(
            content="The Sharpe Ratio measures risk-adjusted return.",
            metadata={'page': 3, 'section': 'Risk Metrics', 'chunk_id': 'chunk_3'},
            embeddings=[0.3] * 3072
        )
    ]
    
    print("\n" + "=" * 80)
    print("PINECONE STORE TEST")
    print("=" * 80 + "\n")
    
    # Initialize store
    store = PineconeStore(
        index_name="test-fintbx",
        dimension=3072,
        batch_size=2
    )
    
    # Create index
    print("Creating index...")
    store.create_index(force=True)
    print()
    
    # Upsert chunks
    print("Upserting chunks...")
    upserted = store.upsert_chunks(sample_chunks, show_progress=True)
    print(f"Upserted {upserted} chunks\n")
    
    # Get index stats
    print("Index stats:")
    stats = store.get_index_stats()
    print(json.dumps(stats, indent=2))
    print()
    
    # Query by text
    print("Querying by text: 'What is the Sharpe Ratio?'")
    results = store.query_by_text("What is the Sharpe Ratio?", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.4f}")
        print(f"   Content: {result['metadata'].get('content', '')[:60]}...")
        print(f"   Section: {result['metadata'].get('section_title', 'N/A')}")
        print()
    
    # Get stats
    print("Storage stats:")
    storage_stats = store.get_stats()
    print(json.dumps(storage_stats, indent=2))
    print()
    
    print("=" * 80)
    print("[OK] Pinecone store test complete!")
    print("=" * 80)
    
    # Cleanup
    response = input("\nDelete test index? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        store.delete_index()
        print("Test index deleted")


if __name__ == '__main__':
    test_pinecone_store()

