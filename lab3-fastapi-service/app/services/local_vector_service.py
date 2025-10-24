"""
Local Vector Store Service for AURELIA RAG
Uses the embedded chunks from lab1 as the primary data source
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from app.models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class LocalVectorService:
    """
    Service for querying local embedded chunks from lab1
    """
    
    def __init__(self):
        """
        Initialize local vector service with lab1 embedded data
        """
        self.chunks_data: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self.chunk_metadata: List[Dict[str, Any]] = []
        self._load_embedded_data()
        
    def _load_embedded_data(self) -> None:
        """
        Load the embedded chunks from lab1 outputs
        """
        try:
            # Path to lab1 embedded chunks
            lab1_path = Path(__file__).parent.parent.parent.parent / "lab1-pdf-processing" / "outputs" / "chunks" / "chunks_markdown_embedded.json"
            
            if not lab1_path.exists():
                logger.warning(f"Lab1 embedded data not found at {lab1_path}")
                return
                
            with open(lab1_path, 'r', encoding='utf-8') as f:
                self.chunks_data = json.load(f)
            
            # Extract embeddings and metadata
            for chunk in self.chunks_data:
                self.embeddings.append(chunk['embeddings'])
                self.chunk_metadata.append(chunk['metadata'])
            
            logger.info(f"Loaded {len(self.chunks_data)} embedded chunks from lab1")
            
        except Exception as e:
            logger.error(f"Failed to load embedded data: {str(e)}")
            self.chunks_data = []
            self.embeddings = []
            self.chunk_metadata = []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def query_chunks(
        self, 
        query_embedding: List[float], 
        top_k: int = 5, 
        threshold: float = 0.7
    ) -> List[RetrievedChunk]:
        """
        Query local chunks using cosine similarity
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of RetrievedChunk objects
        """
        try:
            if not self.chunks_data or not self.embeddings:
                logger.warning("No embedded data available for querying")
                return []
            
            # Calculate similarities
            similarities = []
            for i, chunk_embedding in enumerate(self.embeddings):
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by threshold and get top_k
            results = []
            for i, similarity in similarities:
                if similarity >= threshold and len(results) < top_k:
                    chunk_data = self.chunks_data[i]
                    metadata = self.chunk_metadata[i]
                    
                    # Create RetrievedChunk
                    chunk = RetrievedChunk(
                        content=chunk_data['content'],
                        metadata={
                            'source': metadata.get('source', 'fintbx.pdf'),
                            'chunk_index': metadata.get('chunk_index', i),
                            'strategy': metadata.get('strategy', 'MarkdownHeader'),
                            'headers': metadata.get('headers', {}),
                            'page': metadata.get('page', 'Unknown'),
                            'section': metadata.get('section', 'Unknown')
                        },
                        score=similarity
                    )
                    results.append(chunk)
            
            logger.info(f"Local vector query returned {len(results)} results above threshold {threshold}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying local chunks: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded data
        """
        return {
            'total_chunks': len(self.chunks_data),
            'total_embeddings': len(self.embeddings),
            'embedding_dimension': len(self.embeddings[0]) if self.embeddings else 0,
            'data_source': 'lab1-pdf-processing/outputs/chunks/chunks_markdown_embedded.json'
        }
