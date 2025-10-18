#!/usr/bin/env python3
"""
Base Chunking Framework for AURELIA
Abstract base classes and utilities for text chunking strategies
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import hashlib
import tiktoken


@dataclass
class Chunk:
    """
    Represents a chunk of text with metadata and optional embeddings
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    chunk_id: str = field(init=False)
    
    def __post_init__(self):
        """Generate unique chunk ID based on content and metadata"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        page = self.metadata.get('page', 'unknown')
        chunk_type = self.metadata.get('type', 'text')
        self.chunk_id = f"{chunk_type}_{page}_{content_hash}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'metadata': self.metadata,
            'embeddings': self.embeddings,
            'token_count': self.get_token_count()
        }
    
    def get_token_count(self) -> int:
        """Calculate token count using tiktoken"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-3.5/4 encoding
            return len(encoding.encode(self.content))
        except:
            # Fallback to approximate token count (1 token ≈ 4 characters)
            return len(self.content) // 4


class ChunkStrategy(ABC):
    """
    Abstract base class for chunking strategies
    """
    
    def __init__(self, name: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.name = name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Split text into chunks
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Chunk objects
        """
        pass
    
    @abstractmethod
    def get_chunk_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the chunking strategy
        
        Returns:
            Dictionary with strategy information
        """
        pass


class RecursiveCharacterChunker(ChunkStrategy):
    """
    Chunks text by recursively splitting on different separators
    Good for general-purpose text chunking
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__("RecursiveCharacter", chunk_size, chunk_overlap)
        self.separators = ["\n\n", "\n", ". ", " ", ""]
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text recursively by separators"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )
        
        chunks = splitter.create_documents([text])
        
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': i,
                'strategy': self.name,
                'total_chunks': len(chunks)
            })
            result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
        
        return result
    
    def get_chunk_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'separators': self.separators,
            'description': 'Recursively splits text on multiple separators'
        }


class MarkdownHeaderChunker(ChunkStrategy):
    """
    Chunks markdown text by headers
    Preserves document structure and hierarchy
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__("MarkdownHeader", chunk_size, chunk_overlap)
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text by markdown headers"""
        from langchain.text_splitter import MarkdownHeaderTextSplitter
        
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )
        
        chunks = splitter.split_text(text)
        
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': i,
                'strategy': self.name,
                'total_chunks': len(chunks),
                'headers': chunk.metadata
            })
            result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
        
        return result
    
    def get_chunk_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'headers': [h[0] for h in self.headers_to_split_on],
            'description': 'Splits markdown by headers, preserves structure'
        }


class SectionAwareChunker(ChunkStrategy):
    """
    Chunks text by sections and headings
    Maintains context within sections
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__("SectionAware", chunk_size, chunk_overlap)
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text by sections, preserving section boundaries"""
        import re
        
        # Split by page markers and headings
        sections = re.split(r'(<!-- Page: \d+ -->|^#{1,4}\s+.+$)', text, flags=re.MULTILINE)
        
        chunks = []
        current_section = []
        current_metadata = metadata.copy() if metadata else {}
        section_title = None
        
        for section in sections:
            if not section.strip():
                continue
            
            # Check if it's a page marker
            page_match = re.match(r'<!-- Page: (\d+) -->', section)
            if page_match:
                current_metadata['page'] = int(page_match.group(1))
                continue
            
            # Check if it's a heading
            heading_match = re.match(r'^(#{1,4})\s+(.+)$', section.strip())
            if heading_match:
                level = len(heading_match.group(1))
                section_title = heading_match.group(2)
                current_metadata['section_title'] = section_title
                current_metadata['heading_level'] = level
                continue
            
            # Add content to current section
            current_section.append(section)
            
            # If section is large enough, create chunk
            section_text = '\n'.join(current_section)
            if len(section_text) > self.chunk_size:
                # Split large sections
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                sub_chunks = splitter.create_documents([section_text])
                
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk_metadata = current_metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': i,
                        'strategy': self.name
                    })
                    chunks.append(Chunk(content=sub_chunk.page_content, metadata=chunk_metadata))
                
                current_section = []
        
        # Add remaining content
        if current_section:
            section_text = '\n'.join(current_section)
            chunk_metadata = current_metadata.copy()
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'strategy': self.name
            })
            chunks.append(Chunk(content=section_text, metadata=chunk_metadata))
        
        # Update total chunks count
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)
        
        return chunks
    
    def get_chunk_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'description': 'Splits by sections and headings, preserves context'
        }


class CodeAwareChunker(ChunkStrategy):
    """
    Chunks text with special handling for code blocks
    Preserves code blocks as complete units
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__("CodeAware", chunk_size, chunk_overlap)
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text while preserving code blocks"""
        import re
        
        # Split by code blocks
        parts = re.split(r'(```[\s\S]*?```)', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        current_metadata = metadata.copy() if metadata else {}
        
        for part in parts:
            part_length = len(part)
            
            # If it's a code block, always keep it whole
            if part.startswith('```'):
                if current_length + part_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_metadata = current_metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': chunk_index,
                        'strategy': self.name,
                        'has_code': False
                    })
                    chunks.append(Chunk(
                        content='\n'.join(current_chunk),
                        metadata=chunk_metadata
                    ))
                    chunk_index += 1
                    current_chunk = [part]
                    current_length = part_length
                else:
                    current_chunk.append(part)
                    current_length += part_length
            else:
                # Regular text - can be split
                if current_length + part_length > self.chunk_size:
                    # Split the text part
                    from langchain.text_splitter import RecursiveCharacterTextSplitter
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=self.chunk_size - current_length,
                        chunk_overlap=self.chunk_overlap
                    )
                    text_chunks = splitter.create_documents([part])
                    
                    for i, text_chunk in enumerate(text_chunks):
                        if i == 0:
                            current_chunk.append(text_chunk.page_content)
                            current_length += len(text_chunk.page_content)
                        else:
                            # Save current chunk
                            chunk_metadata = current_metadata.copy()
                            chunk_metadata.update({
                                'chunk_index': chunk_index,
                                'strategy': self.name,
                                'has_code': '```' in '\n'.join(current_chunk)
                            })
                            chunks.append(Chunk(
                                content='\n'.join(current_chunk),
                                metadata=chunk_metadata
                            ))
                            chunk_index += 1
                            current_chunk = [text_chunk.page_content]
                            current_length = len(text_chunk.page_content)
                else:
                    current_chunk.append(part)
                    current_length += part_length
        
        # Add remaining content
        if current_chunk:
            chunk_metadata = current_metadata.copy()
            chunk_metadata.update({
                'chunk_index': chunk_index,
                'strategy': self.name,
                'has_code': '```' in '\n'.join(current_chunk)
            })
            chunks.append(Chunk(
                content='\n'.join(current_chunk),
                metadata=chunk_metadata
            ))
        
        # Update total chunks count
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)
        
        return chunks
    
    def get_chunk_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'description': 'Preserves code blocks as complete units'
        }


# Utility Functions

def calculate_chunk_overlap(chunk1: Chunk, chunk2: Chunk) -> float:
    """
    Calculate overlap between two chunks
    
    Returns:
        Overlap ratio (0.0 to 1.0)
    """
    words1 = set(chunk1.content.lower().split())
    words2 = set(chunk2.content.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def validate_chunk_sizes(chunks: List[Chunk], min_size: int = 100, max_size: int = 2000) -> Dict[str, Any]:
    """
    Validate chunk sizes
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_chunks': len(chunks),
        'valid_chunks': 0,
        'too_small': 0,
        'too_large': 0,
        'avg_size': 0,
        'min_size': float('inf'),
        'max_size': 0,
        'avg_tokens': 0
    }
    
    if not chunks:
        return results
    
    total_size = 0
    total_tokens = 0
    
    for chunk in chunks:
        size = len(chunk.content)
        tokens = chunk.get_token_count()
        
        total_size += size
        total_tokens += tokens
        
        results['min_size'] = min(results['min_size'], size)
        results['max_size'] = max(results['max_size'], size)
        
        if size < min_size:
            results['too_small'] += 1
        elif size > max_size:
            results['too_large'] += 1
        else:
            results['valid_chunks'] += 1
    
    results['avg_size'] = total_size / len(chunks)
    results['avg_tokens'] = total_tokens / len(chunks)
    
    return results


def analyze_chunking_strategy(chunks: List[Chunk]) -> Dict[str, Any]:
    """
    Analyze and compare chunking strategies
    
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'total_chunks': len(chunks),
        'avg_chunk_size': 0,
        'avg_tokens': 0,
        'size_distribution': {},
        'type_distribution': {},
        'strategy': chunks[0].metadata.get('strategy', 'unknown') if chunks else 'none'
    }
    
    if not chunks:
        return analysis
    
    total_size = sum(len(chunk.content) for chunk in chunks)
    total_tokens = sum(chunk.get_token_count() for chunk in chunks)
    
    analysis['avg_chunk_size'] = total_size / len(chunks)
    analysis['avg_tokens'] = total_tokens / len(chunks)
    
    # Size distribution
    for chunk in chunks:
        size = len(chunk.content)
        size_range = f"{(size // 500) * 500}-{(size // 500 + 1) * 500}"
        analysis['size_distribution'][size_range] = analysis['size_distribution'].get(size_range, 0) + 1
        
        chunk_type = chunk.metadata.get('type', 'text')
        analysis['type_distribution'][chunk_type] = analysis['type_distribution'].get(chunk_type, 0) + 1
    
    return analysis


def compare_chunking_strategies(strategy_results: Dict[str, List[Chunk]]) -> Dict[str, Any]:
    """
    Compare multiple chunking strategies
    
    Args:
        strategy_results: Dictionary mapping strategy names to their chunks
        
    Returns:
        Comparison results
    """
    comparison = {}
    
    for strategy_name, chunks in strategy_results.items():
        comparison[strategy_name] = analyze_chunking_strategy(chunks)
    
    return comparison


if __name__ == "__main__":
    # Example usage
    sample_text = """
    # Introduction
    
    This is the introduction section.
    
    ## Overview
    
    Here's some content about the overview.
    
    ```matlab
    function result = example()
        result = 42;
    end
    ```
    
    More text content here.
    """
    
    # Test different strategies
    strategies = [
        RecursiveCharacterChunker(chunk_size=500, chunk_overlap=100),
        MarkdownHeaderChunker(chunk_size=500, chunk_overlap=100),
        SectionAwareChunker(chunk_size=500, chunk_overlap=100),
        CodeAwareChunker(chunk_size=500, chunk_overlap=100)
    ]
    
    print("=" * 70)
    print("Chunking Strategy Comparison")
    print("=" * 70)
    
    for strategy in strategies:
        chunks = strategy.chunk(sample_text, metadata={'source': 'test'})
        validation = validate_chunk_sizes(chunks)
        analysis = analyze_chunking_strategy(chunks)
        
        print(f"\nStrategy: {strategy.name}")
        print(f"  Chunks created: {validation['total_chunks']}")
        print(f"  Avg size: {analysis['avg_chunk_size']:.0f} chars")
        print(f"  Avg tokens: {analysis['avg_tokens']:.0f}")
        print(f"  Valid chunks: {validation['valid_chunks']}/{validation['total_chunks']}")

