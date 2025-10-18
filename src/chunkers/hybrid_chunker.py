"""
Hybrid Chunking Strategy
Intelligently routes content to the most appropriate chunker based on content type
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk, ChunkStrategy
from chunkers.recursive_chunker import RecursiveChunker
from chunkers.markdown_header_chunker import MarkdownHeaderChunker
from chunkers.code_aware_chunker import CodeAwareChunker
from chunkers.semantic_section_chunker import SemanticSectionChunker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContentTypeStats:
    """Statistics about content type distribution"""
    narrative_text: int = 0
    code_blocks: int = 0
    mathematical_formulas: int = 0
    mixed_content: int = 0
    total_chunks: int = 0
    
    def to_dict(self):
        return {
            'narrative_text': self.narrative_text,
            'code_blocks': self.code_blocks,
            'mathematical_formulas': self.mathematical_formulas,
            'mixed_content': self.mixed_content,
            'total_chunks': self.total_chunks
        }


class ContentTypeDetector:
    """Detects content type to determine appropriate chunking strategy"""
    
    def __init__(self, 
                 code_threshold: float = 0.15,
                 formula_threshold: float = 0.10,
                 mixed_threshold: float = 0.20):
        """
        Args:
            code_threshold: Minimum ratio of code to classify as code block
            formula_threshold: Minimum ratio of formulas to classify as formula content
            mixed_threshold: Threshold for mixed content
        """
        self.code_threshold = code_threshold
        self.formula_threshold = formula_threshold
        self.mixed_threshold = mixed_threshold
        
        # Patterns for detection
        self.code_patterns = [
            r'```matlab[\s\S]*?```',  # MATLAB code blocks
            r'```python[\s\S]*?```',   # Python code blocks
            r'```[\s\S]*?```',         # Generic code blocks
            r'^\s*>>\s+',               # MATLAB command prompt
            r'function\s+\w+\s*\(',     # Function definitions
            r'^\s*\w+\s*=\s*\[',        # Array assignments
        ]
        
        self.formula_patterns = [
            r'\$\$[\s\S]*?\$\$',       # Block formulas
            r'\$[^\$]+\$',              # Inline formulas
            r'\\begin\{equation\}[\s\S]*?\\end\{equation\}',  # LaTeX equations
            r'\\begin\{align\}[\s\S]*?\\end\{align\}',        # LaTeX align
            r'\\frac\{[^}]+\}\{[^}]+\}',  # Fractions
            r'\\sum_\{[^}]+\}\^\{[^}]+\}',  # Summations
        ]
        
        self.heading_patterns = [
            r'^#{1,4}\s+.+$',          # Markdown headings
            r'^[A-Z][^.!?]*$',         # All caps lines
        ]
    
    def detect_content_type(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Detect the primary content type
        
        Returns:
            Tuple of (content_type, confidence_scores)
        """
        text_length = len(text)
        if text_length == 0:
            return 'narrative_text', {'narrative_text': 1.0}
        
        # Calculate ratios
        code_ratio = self._calculate_code_ratio(text, text_length)
        formula_ratio = self._calculate_formula_ratio(text, text_length)
        heading_ratio = self._calculate_heading_ratio(text, text_length)
        
        # Determine content type
        if code_ratio >= self.code_threshold:
            content_type = 'code_blocks'
            confidence = code_ratio
        elif formula_ratio >= self.formula_threshold:
            content_type = 'mathematical_formulas'
            confidence = formula_ratio
        elif heading_ratio >= 0.05 and (code_ratio + formula_ratio) < self.mixed_threshold:
            content_type = 'narrative_text'
            confidence = heading_ratio
        elif (code_ratio + formula_ratio) >= self.mixed_threshold:
            content_type = 'mixed_content'
            confidence = code_ratio + formula_ratio
        else:
            content_type = 'narrative_text'
            confidence = 1.0 - (code_ratio + formula_ratio)
        
        scores = {
            'code_blocks': code_ratio,
            'mathematical_formulas': formula_ratio,
            'narrative_text': 1.0 - (code_ratio + formula_ratio),
            'mixed_content': code_ratio + formula_ratio
        }
        
        logger.debug(f"Content type: {content_type}, confidence: {confidence:.2f}, scores: {scores}")
        
        return content_type, scores
    
    def _calculate_code_ratio(self, text: str, text_length: int) -> float:
        """Calculate ratio of code content"""
        code_length = 0
        for pattern in self.code_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            code_length += sum(len(match) for match in matches)
        return code_length / text_length if text_length > 0 else 0.0
    
    def _calculate_formula_ratio(self, text: str, text_length: int) -> float:
        """Calculate ratio of formula content"""
        formula_length = 0
        for pattern in self.formula_patterns:
            matches = re.findall(pattern, text)
            formula_length += sum(len(match) for match in matches)
        return formula_length / text_length if text_length > 0 else 0.0
    
    def _calculate_heading_ratio(self, text: str, text_length: int) -> float:
        """Calculate ratio of heading content"""
        heading_length = 0
        for pattern in self.heading_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            heading_length += sum(len(match) for match in matches)
        return heading_length / text_length if text_length > 0 else 0.0


class HybridChunker(ChunkStrategy):
    """
    Hybrid chunking strategy that routes content to appropriate chunker
    based on content type detection
    """
    
    def __init__(self,
                 # Chunking parameters
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 
                 # Content detection thresholds
                 code_threshold: float = 0.15,
                 formula_threshold: float = 0.10,
                 mixed_threshold: float = 0.20,
                 
                 # Strategy-specific configs
                 recursive_config: Optional[Dict] = None,
                 markdown_config: Optional[Dict] = None,
                 code_config: Optional[Dict] = None,
                 semantic_config: Optional[Dict] = None,
                 
                 # Logging
                 log_routing: bool = True,
                 
                 # Metadata
                 source: str = 'hybrid_chunker'):
        """
        Initialize hybrid chunker
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            code_threshold: Minimum code ratio to use code-aware chunker
            formula_threshold: Minimum formula ratio to use semantic chunker
            mixed_threshold: Threshold for mixed content
            recursive_config: Config for recursive chunker
            markdown_config: Config for markdown chunker
            code_config: Config for code-aware chunker
            semantic_config: Config for semantic chunker
            log_routing: Whether to log routing decisions
            source: Source identifier for metadata
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.source = source
        self.log_routing = log_routing
        
        # Initialize content type detector
        self.detector = ContentTypeDetector(
            code_threshold=code_threshold,
            formula_threshold=formula_threshold,
            mixed_threshold=mixed_threshold
        )
        
        # Initialize individual chunkers
        self.recursive_chunker = RecursiveChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.markdown_chunker = MarkdownHeaderChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.code_chunker = CodeAwareChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.semantic_chunker = SemanticSectionChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Routing statistics
        self.routing_stats = ContentTypeStats()
        
        logger.info(f"Initialized HybridChunker with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Chunk text using hybrid strategy
        
        Args:
            text: Text to chunk
            metadata: Optional metadata
            
        Returns:
            List of Chunk objects
        """
        if metadata is None:
            metadata = {}
        
        # Detect content type
        content_type, confidence_scores = self.detector.detect_content_type(text)
        
        # Log routing decision
        if self.log_routing:
            logger.info(f"Routing to {content_type} chunker (confidence: {confidence_scores.get(content_type, 0):.2f})")
        
        # Route to appropriate chunker
        if content_type == 'code_blocks':
            chunks = self.code_chunker.chunk(text, metadata)
            self.routing_stats.code_blocks += len(chunks)
        elif content_type == 'mathematical_formulas':
            chunks = self.semantic_chunker.chunk(text, metadata)
            self.routing_stats.mathematical_formulas += len(chunks)
        elif content_type == 'narrative_text':
            chunks = self.markdown_chunker.chunk(text, metadata)
            self.routing_stats.narrative_text += len(chunks)
        else:  # mixed_content
            chunks = self.recursive_chunker.chunk(text, metadata)
            self.routing_stats.mixed_content += len(chunks)
        
        self.routing_stats.total_chunks += len(chunks)
        
        # Enrich metadata with routing information
        for chunk in chunks:
            chunk.metadata['routing_strategy'] = content_type
            chunk.metadata['routing_confidence'] = confidence_scores.get(content_type, 0)
            chunk.metadata['routing_scores'] = confidence_scores
        
        return chunks
    
    def chunk_by_section(self, sections: List[Dict[str, Any]]) -> List[Chunk]:
        """
        Chunk multiple sections with intelligent routing
        
        Args:
            sections: List of section dicts with 'content' and 'metadata'
            
        Returns:
            List of Chunk objects
        """
        all_chunks = []
        
        for section in sections:
            content = section.get('content', '')
            metadata = section.get('metadata', {})
            
            # Chunk this section
            chunks = self.chunk(content, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def get_chunk_metadata(self, chunk: Chunk) -> Dict[str, Any]:
        """Get metadata for a chunk"""
        return chunk.metadata
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions"""
        stats = self.routing_stats.to_dict()
        
        # Add percentages
        if stats['total_chunks'] > 0:
            stats['percentages'] = {
                'narrative_text': (stats['narrative_text'] / stats['total_chunks']) * 100,
                'code_blocks': (stats['code_blocks'] / stats['total_chunks']) * 100,
                'mathematical_formulas': (stats['mathematical_formulas'] / stats['total_chunks']) * 100,
                'mixed_content': (stats['mixed_content'] / stats['total_chunks']) * 100
            }
        
        return stats
    
    def reset_stats(self):
        """Reset routing statistics"""
        self.routing_stats = ContentTypeStats()
        logger.info("Routing statistics reset")


def test_hybrid_chunker():
    """Test the hybrid chunker with different content types"""
    
    # Test cases
    test_cases = [
        {
            'name': 'Narrative Text',
            'content': """
# Introduction to Financial Toolbox

The Financial Toolbox provides comprehensive functions for financial analysis.
This guide covers various topics including portfolio optimization, risk management,
and derivative pricing.

## Key Features

- Portfolio optimization
- Risk analysis
- Derivative pricing
- Time series analysis
            """,
            'expected_type': 'narrative_text'
        },
        {
            'name': 'Code Block',
            'content': """
Here's how to calculate present value:

```matlab
>> price = 100;
>> rate = 0.05;
>> duration = 5;
>> pv = price / (1 + rate)^duration;
>> disp(pv);
```

This formula is fundamental to finance.
            """,
            'expected_type': 'code_blocks'
        },
        {
            'name': 'Mathematical Formula',
            'content': """
## Duration Formula

The modified duration is calculated as:

$$D_m = \\frac{D}{1 + y}$$

Where:
- $D$ is the Macaulay duration
- $y$ is the yield to maturity

For continuous compounding:

$$D_c = \\frac{1}{P} \\sum_{t=1}^{n} t \\cdot CF_t \\cdot e^{-yt}$$
            """,
            'expected_type': 'mathematical_formulas'
        },
        {
            'name': 'Mixed Content',
            'content': """
## Sharpe Ratio

The Sharpe Ratio measures risk-adjusted return:

$$SR = \\frac{R_p - R_f}{\\sigma_p}$$

Where $R_p$ is portfolio return, $R_f$ is risk-free rate, and $\\sigma_p$ is portfolio volatility.

```matlab
>> returns = [0.05, 0.08, 0.03, 0.12];
>> sharpe = sharpeRatio(returns, 0.02);
>> disp(sharpe);
```

This metric is widely used in portfolio analysis.
            """,
            'expected_type': 'mixed_content'
        }
    ]
    
    # Initialize chunker
    chunker = HybridChunker(
        chunk_size=1000,
        chunk_overlap=200,
        log_routing=True
    )
    
    print("\n" + "="*80)
    print("HYBRID CHUNKER TEST")
    print("="*80 + "\n")
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 80)
        
        # Detect content type
        content_type, scores = chunker.detector.detect_content_type(test_case['content'])
        
        print(f"Expected: {test_case['expected_type']}")
        print(f"Detected: {content_type}")
        print(f"Confidence scores: {scores}")
        
        # Chunk the content
        chunks = chunker.chunk(test_case['content'], {'test': test_case['name']})
        
        print(f"Generated {len(chunks)} chunks")
        print(f"First chunk routing: {chunks[0].metadata.get('routing_strategy')}")
        print()
    
    # Print routing statistics
    print("="*80)
    print("ROUTING STATISTICS")
    print("="*80)
    stats = chunker.get_routing_stats()
    print(json.dumps(stats, indent=2))
    print()
    
    # Save test results
    output_dir = Path('outputs/chunking_tests')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_results = {
        'test_cases': [
            {
                'name': tc['name'],
                'expected_type': tc['expected_type'],
                'detected_type': chunker.detector.detect_content_type(tc['content'])[0],
                'chunks_generated': len(chunker.chunk(tc['content']))
            }
            for tc in test_cases
        ],
        'routing_stats': stats
    }
    
    with open(output_dir / 'hybrid_chunker_test.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"[OK] Test results saved to: {output_dir / 'hybrid_chunker_test.json'}")


if __name__ == '__main__':
    test_hybrid_chunker()

