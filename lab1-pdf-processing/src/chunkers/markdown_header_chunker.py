#!/usr/bin/env python3
"""
Strategy 2: MarkdownHeaderTextSplitter
Structure-aware chunking based on markdown headers
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk, ChunkStrategy


class MarkdownHeaderChunker(ChunkStrategy):
    """
    MarkdownHeaderTextSplitter implementation
    Splits text based on markdown heading levels
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        headers_to_split_on: List[Tuple[str, str]] = None,
        combine_with_recursive: bool = False
    ):
        super().__init__("MarkdownHeader", chunk_size, chunk_overlap)
        self.headers_to_split_on = headers_to_split_on or [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        self.combine_with_recursive = combine_with_recursive
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )
        if combine_with_recursive:
            self.recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text by markdown headers"""
        # First split by headers
        header_chunks = self.header_splitter.split_text(text)
        
        result = []
        chunk_index = 0
        
        for header_chunk in header_chunks:
            # If combining with recursive, split large sections
            if self.combine_with_recursive and len(header_chunk.page_content) > self.chunk_size:
                sub_chunks = self.recursive_splitter.create_documents([header_chunk.page_content])
                
                for sub_chunk in sub_chunks:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        'chunk_index': chunk_index,
                        'strategy': self.name,
                        'headers': header_chunk.metadata,
                        'type': 'text'
                    })
                    result.append(Chunk(content=sub_chunk.page_content, metadata=chunk_metadata))
                    chunk_index += 1
            else:
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': chunk_index,
                    'strategy': self.name,
                    'headers': header_chunk.metadata,
                    'type': 'text'
                })
                result.append(Chunk(content=header_chunk.page_content, metadata=chunk_metadata))
                chunk_index += 1
        
        # Update total chunks count
        for chunk in result:
            chunk.metadata['total_chunks'] = len(result)
        
        return result
    
    def get_chunk_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'headers': [h[0] for h in self.headers_to_split_on],
            'combine_with_recursive': self.combine_with_recursive,
            'description': 'Splits markdown by headers, preserves structure'
        }


def test_hierarchy_preservation(text: str) -> Dict[str, Any]:
    """
    Test how well the chunker preserves section hierarchy
    
    Returns:
        Dictionary with test results
    """
    chunker = MarkdownHeaderChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk(text)
    
    hierarchy_stats = {
        'h1_sections': 0,
        'h2_sections': 0,
        'h3_sections': 0,
        'h4_sections': 0,
        'chunks_with_headers': 0,
        'chunks_without_headers': 0
    }
    
    for chunk in chunks:
        headers = chunk.metadata.get('headers', {})
        
        if headers:
            hierarchy_stats['chunks_with_headers'] += 1
            for key in headers.keys():
                if 'Header 1' in key:
                    hierarchy_stats['h1_sections'] += 1
                elif 'Header 2' in key:
                    hierarchy_stats['h2_sections'] += 1
                elif 'Header 3' in key:
                    hierarchy_stats['h3_sections'] += 1
                elif 'Header 4' in key:
                    hierarchy_stats['h4_sections'] += 1
        else:
            hierarchy_stats['chunks_without_headers'] += 1
    
    return hierarchy_stats


def test_different_header_levels(
    text: str,
    max_header_level: int = 4
) -> List[Dict[str, Any]]:
    """
    Test chunking with different header level thresholds
    
    Returns:
        List of results for each configuration
    """
    results = []
    
    for level in range(1, max_header_level + 1):
        headers = [(f"{'#' * i}", f"Header {i}") for i in range(1, level + 1)]
        
        chunker = MarkdownHeaderChunker(
            chunk_size=1000,
            chunk_overlap=200,
            headers_to_split_on=headers
        )
        chunks = chunker.chunk(text)
        
        avg_size = sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0
        avg_tokens = sum(c.get_token_count() for c in chunks) / len(chunks) if chunks else 0
        
        results.append({
            'max_header_level': level,
            'total_chunks': len(chunks),
            'avg_size': round(avg_size, 2),
            'avg_tokens': round(avg_tokens, 2)
        })
    
    return results


def main():
    """Test and demonstrate MarkdownHeaderChunker"""
    
    # Sample markdown text with hierarchy
    sample_text = """
# Financial Toolbox User's Guide

## Chapter 1: Introduction

### 1.1 Overview
The Financial Toolbox provides comprehensive tools for quantitative finance.

### 1.2 Key Features
- Portfolio optimization
- Risk analysis
- Derivative pricing

## Chapter 2: Getting Started

### 2.1 Installation
Install the toolbox using MATLAB's package manager.

### 2.2 First Example

```matlab
>> price = 100;
>> rate = 0.05;
>> pv = price / (1 + rate)^5;
```

## Chapter 3: Advanced Topics

### 3.1 Portfolio Theory
Modern portfolio theory is fundamental to quantitative finance.

#### 3.1.1 Risk-Return Tradeoff
The risk-return tradeoff is a key concept.

#### 3.1.2 Efficient Frontier
The efficient frontier represents optimal portfolios.

### 3.2 Options Pricing

```matlab
function price = black_scholes(S, K, r, T, sigma)
    % Black-Scholes formula
    d1 = (log(S/K) + (r + sigma^2/2)*T) / (sigma*sqrt(T));
    d2 = d1 - sigma*sqrt(T);
    price = S*normcdf(d1) - K*exp(-r*T)*normcdf(d2);
end
```

## Conclusion
The Financial Toolbox provides essential tools for financial analysis.
"""
    
    print("=" * 70)
    print("MarkdownHeaderTextSplitter - Testing & Demonstration")
    print("=" * 70)
    
    # Test 1: Basic header chunking
    print("\n1. Basic Header Chunking")
    chunker = MarkdownHeaderChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk(sample_text, metadata={'source': 'test'})
    print(f"   Created {len(chunks)} chunks")
    print(f"   Avg size: {sum(len(c.content) for c in chunks) / len(chunks):.0f} chars")
    print(f"   Avg tokens: {sum(c.get_token_count() for c in chunks) / len(chunks):.0f}")
    
    # Test 2: Hierarchy preservation
    print("\n2. Hierarchy Preservation Test")
    hierarchy_stats = test_hierarchy_preservation(sample_text)
    print(f"   H1 sections: {hierarchy_stats['h1_sections']}")
    print(f"   H2 sections: {hierarchy_stats['h2_sections']}")
    print(f"   H3 sections: {hierarchy_stats['h3_sections']}")
    print(f"   H4 sections: {hierarchy_stats['h4_sections']}")
    print(f"   Chunks with headers: {hierarchy_stats['chunks_with_headers']}")
    print(f"   Chunks without headers: {hierarchy_stats['chunks_without_headers']}")
    
    # Test 3: Different header levels
    print("\n3. Testing Different Header Levels")
    header_tests = test_different_header_levels(sample_text)
    for test in header_tests:
        print(f"   Max level {test['max_header_level']}: "
              f"{test['total_chunks']} chunks, {test['avg_tokens']:.0f} tokens avg")
    
    # Test 4: Combined with recursive
    print("\n4. Combined with RecursiveCharacterTextSplitter")
    combined_chunker = MarkdownHeaderChunker(
        chunk_size=500,
        chunk_overlap=100,
        combine_with_recursive=True
    )
    combined_chunks = combined_chunker.chunk(sample_text)
    print(f"   Created {len(combined_chunks)} chunks")
    print(f"   Avg size: {sum(len(c.content) for c in combined_chunks) / len(combined_chunks):.0f} chars")
    
    # Test 5: Show example chunks with hierarchy
    print("\n5. Example Chunks with Hierarchy")
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n   Chunk {i}:")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Headers: {chunk.metadata.get('headers', {})}")
        print(f"   Size: {len(chunk.content)} chars, {chunk.get_token_count()} tokens")
        print(f"   Preview: {chunk.content[:150]}...")
    
    # Save results
    output_dir = Path("outputs/chunking_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save chunks
    chunks_data = [c.to_dict() for c in chunks]
    with open(output_dir / "markdown_header_example_chunks.json", 'w') as f:
        json.dump(chunks_data, f, indent=2)
    
    # Save hierarchy stats
    with open(output_dir / "markdown_header_hierarchy_stats.json", 'w') as f:
        json.dump(hierarchy_stats, f, indent=2)
    
    # Save header level tests
    with open(output_dir / "markdown_header_level_tests.json", 'w') as f:
        json.dump(header_tests, f, indent=2)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] MarkdownHeaderTextSplitter Testing Complete!")
    print("=" * 70)
    print(f"Results saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()

