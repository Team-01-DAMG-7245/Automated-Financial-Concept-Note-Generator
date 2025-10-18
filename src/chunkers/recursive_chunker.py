#!/usr/bin/env python3
"""
Strategy 1: RecursiveCharacterTextSplitter
General-purpose chunking with configurable sizes and overlaps
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk, ChunkStrategy


class RecursiveChunker(ChunkStrategy):
    """
    RecursiveCharacterTextSplitter implementation
    Splits text recursively on multiple separators
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        super().__init__("RecursiveCharacter", chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text recursively by separators"""
        chunks = self.splitter.create_documents([text])
        
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': i,
                'strategy': self.name,
                'total_chunks': len(chunks),
                'type': 'text'
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


def benchmark_configurations(
    text: str,
    chunk_sizes: List[int] = [500, 1000, 1500, 2000],
    chunk_overlaps: List[int] = [50, 100, 200, 300],
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Benchmark different chunk size and overlap configurations
    
    Returns:
        List of benchmark results
    """
    results = []
    
    for chunk_size in chunk_sizes:
        for chunk_overlap in chunk_overlaps:
            if chunk_overlap >= chunk_size:
                continue  # Skip invalid configurations
            
            chunker = RecursiveChunker(chunk_size, chunk_overlap)
            chunks = chunker.chunk(text, metadata)
            
            # Calculate statistics
            total_chars = sum(len(c.content) for c in chunks)
            avg_size = total_chars / len(chunks) if chunks else 0
            avg_tokens = sum(c.get_token_count() for c in chunks) / len(chunks) if chunks else 0
            
            # Calculate overlap efficiency
            overlap_efficiency = (chunk_overlap / chunk_size) * 100 if chunk_size > 0 else 0
            
            results.append({
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'total_chunks': len(chunks),
                'avg_size': round(avg_size, 2),
                'avg_tokens': round(avg_tokens, 2),
                'overlap_efficiency': round(overlap_efficiency, 2),
                'total_chars': total_chars
            })
    
    return results


def test_code_preservation(text: str) -> Dict[str, Any]:
    """
    Test how well the chunker preserves code blocks
    
    Returns:
        Dictionary with test results
    """
    chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk(text)
    
    broken_code_blocks = 0
    preserved_code_blocks = 0
    
    for chunk in chunks:
        # Count code blocks
        code_blocks = chunk.content.count('```')
        if code_blocks % 2 != 0:  # Odd number means broken
            broken_code_blocks += 1
        elif code_blocks > 0:
            preserved_code_blocks += code_blocks // 2
    
    return {
        'total_chunks': len(chunks),
        'broken_code_blocks': broken_code_blocks,
        'preserved_code_blocks': preserved_code_blocks,
        'preservation_rate': round((preserved_code_blocks / (preserved_code_blocks + broken_code_blocks)) * 100, 2) if (preserved_code_blocks + broken_code_blocks) > 0 else 0
    }


def main():
    """Test and benchmark RecursiveChunker"""
    
    # Sample text with different content types
    sample_text = """
# Financial Toolbox Introduction

## Overview
The Financial Toolbox provides comprehensive tools for financial analysis.

## Example 1: Basic Calculation

Here's a simple MATLAB example:

```matlab
>> price = 100;
>> rate = 0.05;
>> duration = 5;
>> pv = price / (1 + rate)^duration;
>> disp(pv);
```

The present value calculation is fundamental to finance.

## Example 2: Portfolio Analysis

```matlab
function portfolio_return = calculate_return(prices, weights)
    % Calculate portfolio return
    returns = diff(prices) ./ prices(1:end-1);
    portfolio_return = sum(returns .* weights);
end
```

This function calculates weighted portfolio returns.

## Mathematical Formulas

The Sharpe Ratio is defined as:

$$SR = \\frac{R_p - R_f}{\\sigma_p}$$

Where $R_p$ is the portfolio return, $R_f$ is the risk-free rate, and $\\sigma_p$ is the portfolio volatility.

## Conclusion

The Financial Toolbox provides essential tools for quantitative finance.
"""
    
    print("=" * 70)
    print("RecursiveCharacterTextSplitter - Testing & Benchmarking")
    print("=" * 70)
    
    # Test 1: Basic chunking
    print("\n1. Basic Chunking Test")
    chunker = RecursiveChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk(sample_text, metadata={'source': 'test'})
    print(f"   Created {len(chunks)} chunks")
    print(f"   Avg size: {sum(len(c.content) for c in chunks) / len(chunks):.0f} chars")
    print(f"   Avg tokens: {sum(c.get_token_count() for c in chunks) / len(chunks):.0f}")
    
    # Test 2: Code preservation
    print("\n2. Code Preservation Test")
    code_test = test_code_preservation(sample_text)
    print(f"   Total chunks: {code_test['total_chunks']}")
    print(f"   Broken code blocks: {code_test['broken_code_blocks']}")
    print(f"   Preserved code blocks: {code_test['preserved_code_blocks']}")
    print(f"   Preservation rate: {code_test['preservation_rate']}%")
    
    # Test 3: Benchmark configurations
    print("\n3. Configuration Benchmarking")
    benchmarks = benchmark_configurations(sample_text)
    
    print("\n   Top 5 configurations by chunk count:")
    sorted_benchmarks = sorted(benchmarks, key=lambda x: x['total_chunks'])
    for i, bench in enumerate(sorted_benchmarks[:5], 1):
        print(f"   {i}. Size={bench['chunk_size']}, Overlap={bench['chunk_overlap']}: "
              f"{bench['total_chunks']} chunks, {bench['avg_tokens']:.0f} tokens avg")
    
    print("\n   Top 5 configurations by efficiency:")
    sorted_benchmarks = sorted(benchmarks, key=lambda x: x['overlap_efficiency'], reverse=True)
    for i, bench in enumerate(sorted_benchmarks[:5], 1):
        print(f"   {i}. Size={bench['chunk_size']}, Overlap={bench['chunk_overlap']}: "
              f"{bench['overlap_efficiency']}% efficiency")
    
    # Test 4: Show example chunks
    print("\n4. Example Chunks")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n   Chunk {i}:")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Size: {len(chunk.content)} chars, {chunk.get_token_count()} tokens")
        print(f"   Preview: {chunk.content[:100]}...")
    
    # Save results
    output_dir = Path("outputs/chunking_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save benchmark results
    with open(output_dir / "recursive_benchmark.json", 'w') as f:
        json.dump(benchmarks, f, indent=2)
    
    # Save example chunks
    chunks_data = [c.to_dict() for c in chunks]
    with open(output_dir / "recursive_example_chunks.json", 'w') as f:
        json.dump(chunks_data, f, indent=2)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] RecursiveCharacterTextSplitter Testing Complete!")
    print("=" * 70)
    print(f"Results saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()

