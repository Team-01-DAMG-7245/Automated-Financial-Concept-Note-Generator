#!/usr/bin/env python3
"""
Strategy 4: Semantic Section Chunker
Concept-based splitting that keeps related content together
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk, ChunkStrategy


class SemanticSectionChunker(ChunkStrategy):
    """
    Semantic chunker that identifies concept boundaries
    Keeps related content together (definitions, examples, formulas)
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_chunk_size: int = 2000
    ):
        super().__init__("SemanticSection", chunk_size, chunk_overlap)
        self.max_chunk_size = max_chunk_size
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def detect_semantic_boundaries(self, text: str) -> List[Tuple[int, str, str]]:
        """
        Detect semantic boundaries in text
        
        Returns:
            List of (position, boundary_type, content) tuples
        """
        boundaries = []
        
        # Pattern for different semantic markers
        patterns = [
            (r'^(#+\s+.+)$', 'heading'),  # Headings
            (r'^Example\s+\d+:', 'example'),  # Examples
            (r'^Definition\s+\d+:', 'definition'),  # Definitions
            (r'^```[\s\S]*?```', 'code_block'),  # Code blocks
            (r'\$\$[\s\S]*?\$\$', 'formula'),  # Formulas
            (r'<!-- Page: \d+ -->', 'page_marker'),  # Page markers
        ]
        
        for pattern, boundary_type in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                content = match.group(0)
                boundaries.append((start, boundary_type, content))
        
        # Sort by position
        boundaries.sort(key=lambda x: x[0])
        
        return boundaries
    
    def classify_chunk_type(self, content: str) -> str:
        """
        Classify chunk type based on content
        
        Returns:
            Chunk type: 'definition', 'example', 'formula', 'code', 'reference', 'text'
        """
        content_lower = content.lower()
        
        if '```' in content:
            return 'code'
        if '$$' in content or re.search(r'[∫∑∏√∞≤≥≠≈]', content):
            return 'formula'
        if 'example' in content_lower and ('```' in content or '>>' in content):
            return 'example'
        if 'definition' in content_lower or 'is defined as' in content_lower:
            return 'definition'
        if 'see also' in content_lower or 'reference' in content_lower:
            return 'reference'
        
        return 'text'
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text by semantic boundaries"""
        boundaries = self.detect_semantic_boundaries(text)
        
        if not boundaries:
            # No semantic boundaries, use regular chunking
            chunks = self.text_splitter.create_documents([text])
            result = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': i,
                    'strategy': self.name,
                    'chunk_type': self.classify_chunk_type(chunk.page_content),
                    'type': 'text'
                })
                result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
            
            for chunk in result:
                chunk.metadata['total_chunks'] = len(result)
            
            return result
        
        # Process text with semantic boundaries
        result = []
        last_end = 0
        current_section = []
        current_type = 'text'
        chunk_index = 0
        
        for i, (boundary_pos, boundary_type, boundary_content) in enumerate(boundaries):
            # Add text before boundary
            text_before = text[last_end:boundary_pos]
            if text_before.strip():
                current_section.append(text_before)
            
            # Add boundary content
            current_section.append(boundary_content)
            
            # Update current type based on boundary
            if boundary_type in ['heading', 'example', 'definition', 'formula', 'code_block']:
                current_type = boundary_type
            
            # Check if section is complete
            section_text = '\n'.join(current_section)
            
            # If next boundary is far or section is large enough, create chunk
            if i < len(boundaries) - 1:
                next_pos = boundaries[i + 1][0]
                distance = next_pos - boundary_pos
                
                if len(section_text) > self.chunk_size or distance > 500:
                    # Create chunk
                    chunk_type = self.classify_chunk_type(section_text)
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        'chunk_index': chunk_index,
                        'strategy': self.name,
                        'chunk_type': chunk_type,
                        'type': 'semantic'
                    })
                    result.append(Chunk(content=section_text, metadata=chunk_metadata))
                    chunk_index += 1
                    current_section = []
                    current_type = 'text'
            else:
                # Last boundary, create final chunk
                chunk_type = self.classify_chunk_type(section_text)
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': chunk_index,
                    'strategy': self.name,
                    'chunk_type': chunk_type,
                    'type': 'semantic'
                })
                result.append(Chunk(content=section_text, metadata=chunk_metadata))
                chunk_index += 1
            
            last_end = boundary_pos + len(boundary_content)
        
        # Add remaining text
        text_after = text[last_end:]
        if text_after.strip():
            chunk_type = self.classify_chunk_type(text_after)
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': chunk_index,
                'strategy': self.name,
                'chunk_type': chunk_type,
                'type': 'semantic'
            })
            result.append(Chunk(content=text_after, metadata=chunk_metadata))
        
        # Update total chunks count
        for chunk in result:
            chunk.metadata['total_chunks'] = len(result)
        
        return result
    
    def get_chunk_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'max_chunk_size': self.max_chunk_size,
            'description': 'Splits by semantic boundaries, keeps related content together'
        }


def test_financial_concepts(text: str, concepts: List[str]) -> Dict[str, Any]:
    """
    Test chunking on specific financial concepts
    
    Returns:
        Dictionary with test results
    """
    chunker = SemanticSectionChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk(text)
    
    concept_coverage = {}
    
    for concept in concepts:
        concept_chunks = []
        for chunk in chunks:
            if concept.lower() in chunk.content.lower():
                concept_chunks.append({
                    'chunk_id': chunk.chunk_id,
                    'chunk_type': chunk.metadata.get('chunk_type', 'unknown'),
                    'size': len(chunk.content),
                    'tokens': chunk.get_token_count()
                })
        
        concept_coverage[concept] = {
            'total_chunks': len(concept_chunks),
            'chunks': concept_chunks
        }
    
    return concept_coverage


def main():
    """Test and demonstrate SemanticSectionChunker"""
    
    # Sample text with financial concepts
    sample_text = """
# Financial Concepts Guide

## Duration

### Definition
Duration is a measure of the sensitivity of a bond's price to changes in interest rates.

The duration formula is:

$$D = \\frac{1}{P} \\sum_{t=1}^{T} \\frac{t \\cdot CF_t}{(1+r)^t}$$

Where P is the bond price, CF_t is the cash flow at time t, and r is the yield.

### Example 1: Calculating Duration

```matlab
>> price = 100;
>> coupon = 0.05;
>> yield_rate = 0.04;
>> years = 5;
>> duration = calculate_duration(price, coupon, yield_rate, years);
>> disp(duration);
```

This example demonstrates duration calculation.

## Sharpe Ratio

### Definition
The Sharpe Ratio measures risk-adjusted return.

$$SR = \\frac{R_p - R_f}{\\sigma_p}$$

Where R_p is portfolio return, R_f is risk-free rate, and σ_p is portfolio volatility.

### Example 2: Sharpe Ratio Calculation

```matlab
function sr = sharpe_ratio(returns, risk_free_rate)
    % Calculate Sharpe Ratio
    excess_returns = returns - risk_free_rate;
    sr = mean(excess_returns) / std(excess_returns);
end
```

## Black-Scholes Model

### Definition
The Black-Scholes model prices European options.

### Formula

$$C = S_0 N(d_1) - K e^{-rT} N(d_2)$$

Where:
- S_0 is current stock price
- K is strike price
- r is risk-free rate
- T is time to maturity
- N() is cumulative normal distribution

### Example 3: Options Pricing

```matlab
function price = black_scholes(S, K, r, T, sigma)
    d1 = (log(S/K) + (r + sigma^2/2)*T) / (sigma*sqrt(T));
    d2 = d1 - sigma*sqrt(T);
    price = S*normcdf(d1) - K*exp(-r*T)*normcdf(d2);
end
```

## Conclusion
These concepts are fundamental to quantitative finance.
"""
    
    print("=" * 70)
    print("Semantic Section Chunker - Testing & Demonstration")
    print("=" * 70)
    
    # Test 1: Basic semantic chunking
    print("\n1. Basic Semantic Chunking")
    chunker = SemanticSectionChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk(sample_text, metadata={'source': 'test'})
    print(f"   Created {len(chunks)} chunks")
    print(f"   Avg size: {sum(len(c.content) for c in chunks) / len(chunks):.0f} chars")
    print(f"   Avg tokens: {sum(c.get_token_count() for c in chunks) / len(chunks):.0f}")
    
    # Test 2: Chunk type distribution
    print("\n2. Chunk Type Distribution")
    type_distribution = {}
    for chunk in chunks:
        chunk_type = chunk.metadata.get('chunk_type', 'unknown')
        type_distribution[chunk_type] = type_distribution.get(chunk_type, 0) + 1
    
    for chunk_type, count in sorted(type_distribution.items()):
        print(f"   {chunk_type}: {count}")
    
    # Test 3: Financial concept coverage
    print("\n3. Financial Concept Coverage")
    concepts = ['Duration', 'Sharpe Ratio', 'Black-Scholes']
    concept_coverage = test_financial_concepts(sample_text, concepts)
    
    for concept, coverage in concept_coverage.items():
        print(f"   {concept}:")
        print(f"     - Covered in {coverage['total_chunks']} chunks")
        if coverage['chunks']:
            for chunk_info in coverage['chunks'][:2]:
                print(f"       * {chunk_info['chunk_type']} ({chunk_info['tokens']} tokens)")
    
    # Test 4: Show example chunks
    print("\n4. Example Chunks")
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n   Chunk {i}:")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Type: {chunk.metadata.get('chunk_type', 'unknown')}")
        print(f"   Size: {len(chunk.content)} chars, {chunk.get_token_count()} tokens")
        print(f"   Preview: {chunk.content[:150]}...")
    
    # Save results
    output_dir = Path("outputs/chunking_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save chunks
    chunks_data = [c.to_dict() for c in chunks]
    with open(output_dir / "semantic_section_example_chunks.json", 'w') as f:
        json.dump(chunks_data, f, indent=2)
    
    # Save concept coverage
    with open(output_dir / "semantic_concept_coverage.json", 'w') as f:
        json.dump(concept_coverage, f, indent=2)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Semantic Section Chunker Testing Complete!")
    print("=" * 70)
    print(f"Results saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()

