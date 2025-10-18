#!/usr/bin/env python3
"""
Strategy 3: Code-Aware Chunker
Preserves MATLAB code blocks as complete units
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


class CodeAwareChunker(ChunkStrategy):
    """
    Code-aware chunker that preserves complete code blocks
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_code_chunk_size: int = 2000,
        include_surrounding_context: bool = True,
        context_paragraphs: int = 2
    ):
        super().__init__("CodeAware", chunk_size, chunk_overlap)
        self.max_code_chunk_size = max_code_chunk_size
        self.include_surrounding_context = include_surrounding_context
        self.context_paragraphs = context_paragraphs
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    def detect_code_blocks(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect code blocks in text
        
        Returns:
            List of (start, end, code_block) tuples
        """
        code_blocks = []
        
        # Match markdown code blocks
        pattern = r'```(?:matlab|python|r)?\n([\s\S]*?)```'
        for match in re.finditer(pattern, text):
            start, end = match.span()
            code_block = match.group(0)
            code_blocks.append((start, end, code_block))
        
        return code_blocks
    
    def extract_surrounding_context(
        self,
        text: str,
        code_start: int,
        code_end: int
    ) -> Tuple[str, str]:
        """
        Extract surrounding context before and after code block
        
        Returns:
            (context_before, context_after) tuple
        """
        if not self.include_surrounding_context:
            return "", ""
        
        # Extract context before
        before_text = text[:code_start]
        before_paragraphs = before_text.split('\n\n')
        context_before = '\n\n'.join(before_paragraphs[-self.context_paragraphs:])
        
        # Extract context after
        after_text = text[code_end:]
        after_paragraphs = after_text.split('\n\n')
        context_after = '\n\n'.join(after_paragraphs[:self.context_paragraphs])
        
        return context_before, context_after
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Split text while preserving code blocks"""
        code_blocks = self.detect_code_blocks(text)
        
        if not code_blocks:
            # No code blocks, use regular chunking
            chunks = self.text_splitter.create_documents([text])
            result = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': i,
                    'strategy': self.name,
                    'has_code': False,
                    'type': 'text'
                })
                result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
            
            for chunk in result:
                chunk.metadata['total_chunks'] = len(result)
            
            return result
        
        # Process text with code blocks
        result = []
        last_end = 0
        chunk_index = 0
        
        for code_start, code_end, code_block in code_blocks:
            # Add text before code block
            text_before = text[last_end:code_start]
            if text_before.strip():
                chunks = self.text_splitter.create_documents([text_before])
                for chunk in chunks:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        'chunk_index': chunk_index,
                        'strategy': self.name,
                        'has_code': False,
                        'type': 'text'
                    })
                    result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
                    chunk_index += 1
            
            # Add code block with context
            context_before, context_after = self.extract_surrounding_context(
                text, code_start, code_end
            )
            
            code_with_context = f"{context_before}\n\n{code_block}\n\n{context_after}".strip()
            
            # Check if code block fits in one chunk
            if len(code_with_context) <= self.max_code_chunk_size:
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': chunk_index,
                    'strategy': self.name,
                    'has_code': True,
                    'type': 'code'
                })
                result.append(Chunk(content=code_with_context, metadata=chunk_metadata))
                chunk_index += 1
            else:
                # Split large code block
                chunks = self.text_splitter.create_documents([code_with_context])
                for chunk in chunks:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        'chunk_index': chunk_index,
                        'strategy': self.name,
                        'has_code': True,
                        'type': 'code'
                    })
                    result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
                    chunk_index += 1
            
            last_end = code_end
        
        # Add remaining text after last code block
        text_after = text[last_end:]
        if text_after.strip():
            chunks = self.text_splitter.create_documents([text_after])
            for chunk in chunks:
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': chunk_index,
                    'strategy': self.name,
                    'has_code': False,
                    'type': 'text'
                })
                result.append(Chunk(content=chunk.page_content, metadata=chunk_metadata))
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
            'max_code_chunk_size': self.max_code_chunk_size,
            'include_surrounding_context': self.include_surrounding_context,
            'context_paragraphs': self.context_paragraphs,
            'description': 'Preserves code blocks as complete units'
        }


def validate_code_blocks(chunks: List[Chunk]) -> Dict[str, Any]:
    """
    Validate that no code blocks are broken
    
    Returns:
        Dictionary with validation results
    """
    broken_blocks = 0
    complete_blocks = 0
    code_chunks = 0
    
    for chunk in chunks:
        if chunk.metadata.get('has_code', False):
            code_chunks += 1
            
            # Check if code block is complete
            code_block_count = chunk.content.count('```')
            if code_block_count % 2 == 0 and code_block_count > 0:
                complete_blocks += code_block_count // 2
            else:
                broken_blocks += 1
    
    return {
        'total_chunks': len(chunks),
        'code_chunks': code_chunks,
        'broken_code_blocks': broken_blocks,
        'complete_code_blocks': complete_blocks,
        'validation_passed': broken_blocks == 0
    }


def main():
    """Test and demonstrate CodeAwareChunker"""
    
    # Sample text with code blocks
    sample_text = """
# Financial Toolbox Examples

## Introduction
The Financial Toolbox provides various functions for quantitative finance.

## Example 1: Simple Calculation

Here's a basic MATLAB example:

```matlab
>> price = 100;
>> rate = 0.05;
>> duration = 5;
>> pv = price / (1 + rate)^duration;
>> disp(pv);
```

This calculates the present value of a future payment.

## Example 2: Portfolio Analysis

The following function calculates portfolio returns:

```matlab
function portfolio_return = calculate_return(prices, weights)
    % Calculate portfolio return
    % Inputs: prices (vector), weights (vector)
    % Output: portfolio_return (scalar)
    
    returns = diff(prices) ./ prices(1:end-1);
    portfolio_return = sum(returns .* weights);
end
```

This function is useful for portfolio optimization.

## Example 3: Options Pricing

```matlab
function price = black_scholes(S, K, r, T, sigma)
    % Black-Scholes formula for European call option
    d1 = (log(S/K) + (r + sigma^2/2)*T) / (sigma*sqrt(T));
    d2 = d1 - sigma*sqrt(T);
    price = S*normcdf(d1) - K*exp(-r*T)*normcdf(d2);
end
```

The Black-Scholes model is fundamental to options pricing.

## Conclusion
These examples demonstrate the power of the Financial Toolbox.
"""
    
    print("=" * 70)
    print("Code-Aware Chunker - Testing & Demonstration")
    print("=" * 70)
    
    # Test 1: Basic code-aware chunking
    print("\n1. Basic Code-Aware Chunking")
    chunker = CodeAwareChunker(
        chunk_size=800,
        chunk_overlap=100,
        max_code_chunk_size=2000,
        include_surrounding_context=True
    )
    chunks = chunker.chunk(sample_text, metadata={'source': 'test'})
    print(f"   Created {len(chunks)} chunks")
    print(f"   Avg size: {sum(len(c.content) for c in chunks) / len(chunks):.0f} chars")
    print(f"   Avg tokens: {sum(c.get_token_count() for c in chunks) / len(chunks):.0f}")
    
    # Test 2: Code block validation
    print("\n2. Code Block Validation")
    validation = validate_code_blocks(chunks)
    print(f"   Total chunks: {validation['total_chunks']}")
    print(f"   Code chunks: {validation['code_chunks']}")
    print(f"   Complete code blocks: {validation['complete_code_blocks']}")
    print(f"   Broken code blocks: {validation['broken_code_blocks']}")
    print(f"   Validation passed: {validation['validation_passed']}")
    
    # Test 3: With/without context
    print("\n3. With vs Without Context")
    chunker_with_context = CodeAwareChunker(
        chunk_size=800,
        include_surrounding_context=True
    )
    chunker_no_context = CodeAwareChunker(
        chunk_size=800,
        include_surrounding_context=False
    )
    
    chunks_with = chunker_with_context.chunk(sample_text)
    chunks_without = chunker_no_context.chunk(sample_text)
    
    print(f"   With context: {len(chunks_with)} chunks")
    print(f"   Without context: {len(chunks_without)} chunks")
    
    # Test 4: Show example chunks
    print("\n4. Example Chunks")
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n   Chunk {i}:")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Has code: {chunk.metadata.get('has_code', False)}")
        print(f"   Type: {chunk.metadata.get('type', 'text')}")
        print(f"   Size: {len(chunk.content)} chars, {chunk.get_token_count()} tokens")
        print(f"   Preview: {chunk.content[:150]}...")
    
    # Save results
    output_dir = Path("outputs/chunking_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save chunks
    chunks_data = [c.to_dict() for c in chunks]
    with open(output_dir / "code_aware_example_chunks.json", 'w') as f:
        json.dump(chunks_data, f, indent=2)
    
    # Save validation results
    with open(output_dir / "code_aware_validation.json", 'w') as f:
        json.dump(validation, f, indent=2)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Code-Aware Chunker Testing Complete!")
    print("=" * 70)
    print(f"Results saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()

