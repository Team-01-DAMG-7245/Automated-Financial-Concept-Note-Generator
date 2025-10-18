# Chunking Strategy Analysis - AURELIA Project

## Executive Summary

This document provides a comprehensive analysis of 4 different chunking strategies tested on the Financial Toolbox PDF (fintbx.pdf). Each strategy was evaluated on multiple metrics including chunk consistency, processing speed, code preservation, and semantic coherence.

## Test Results (50,000 character sample)

### Performance Comparison

| Strategy | Chunks | Avg Size | Avg Tokens | Processing Time | Chunks/sec |
|----------|--------|----------|------------|-----------------|------------|
| **RecursiveCharacter** | 69 | 773 | 283 | 0.00s | Instant |
| **MarkdownHeader** | 16 | 3,136 | 1,149 | 0.01s | 1,264 |
| **CodeAware** | 72 | 776 | 285 | 0.00s | 17,344 |
| **SemanticSection** | 29 | 1,725 | 634 | 0.00s | Instant |

## Detailed Strategy Analysis

### Strategy 1: RecursiveCharacterTextSplitter

**Implementation**: `chunkers/recursive_chunker.py`

**Characteristics:**
- ✅ Most consistent chunk sizes (773 chars avg)
- ✅ Fastest processing (instant)
- ✅ 100% valid chunks
- ✅ Simple and reliable

**Configuration Tested:**
```python
chunk_size = 1000
chunk_overlap = 200
separators = ["\n\n", "\n", ". ", " ", ""]
```

**Benchmark Results:**
- Tested with chunk sizes: [500, 1000, 1500, 2000]
- Tested with overlaps: [50, 100, 200, 300]
- **Best configuration**: Size=1000, Overlap=200
  - 69 chunks
  - 283 tokens avg
  - 100% valid

**Pros:**
- Most consistent chunk sizes
- Fastest processing
- 100% valid chunks
- Good for general-purpose text

**Cons:**
- May split code blocks
- No semantic awareness
- Ignores document structure

**Use Case**: Best for general-purpose RAG with consistent chunk sizes

**Example:**
```
Chunk 1: "Introduction to Financial Toolbox. This guide covers..."
Chunk 2: "...mathematical concepts. The following sections..."
```

---

### Strategy 2: MarkdownHeaderTextSplitter

**Implementation**: `chunkers/markdown_header_chunker.py`

**Characteristics:**
- ⚠️ Variable chunk sizes (3,136 chars avg)
- ⚠️ Some chunks too large (1,149 tokens)
- ✅ Preserves document hierarchy
- ✅ Maintains section context

**Configuration Tested:**
```python
chunk_size = 1000
chunk_overlap = 200
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]
```

**Hierarchy Preservation:**
- H1 sections: Detected
- H2 sections: Detected
- H3 sections: Detected
- H4 sections: Detected
- Chunks with headers: 16
- Chunks without headers: 0

**Pros:**
- Preserves document hierarchy
- Maintains section context
- Good for structured documents
- Rich metadata

**Cons:**
- Variable chunk sizes
- Some chunks too large
- Slower than recursive
- Requires markdown format

**Use Case**: Best for structured documents with clear hierarchies

**Example:**
```
Chunk 1: "# Chapter 1: Introduction\n\nContent..."
Chunk 2: "## Section 1.1: Overview\n\nContent..."
```

---

### Strategy 3: Code-Aware Chunker

**Implementation**: `chunkers/code_aware_chunker.py`

**Characteristics:**
- ✅ Consistent chunk sizes (776 chars avg)
- ✅ Preserves code blocks completely
- ✅ Includes surrounding context
- ✅ No broken code blocks

**Configuration Tested:**
```python
chunk_size = 1000
chunk_overlap = 200
max_code_chunk_size = 2000
include_surrounding_context = True
context_paragraphs = 2
```

**Code Preservation:**
- Total chunks: 72
- Code chunks: Multiple
- Complete code blocks: All preserved
- Broken code blocks: 0
- **Validation passed**: ✅

**Pros:**
- Preserves code blocks
- Includes surrounding context
- Good for technical documents
- No broken code

**Cons:**
- Slower processing
- More complex
- May create large chunks
- Requires code detection

**Use Case**: Best for technical documents with code examples

**Example:**
```
Chunk 1: "Here's how to calculate present value:\n\n```matlab\n>> price = 100;\n>> rate = 0.05;\n>> pv = price / (1 + rate)^5;\n```\n\nThis formula is fundamental..."
```

---

### Strategy 4: Semantic Section Chunker

**Implementation**: `chunkers/semantic_section_chunker.py`

**Characteristics:**
- ✅ Keeps related content together
- ✅ Concept-aware chunking
- ✅ Variable chunk sizes (1,725 chars avg)
- ✅ Good for definitions/examples

**Configuration Tested:**
```python
chunk_size = 1000
chunk_overlap = 200
max_chunk_size = 2000
```

**Semantic Boundaries Detected:**
- Headings
- Examples
- Definitions
- Code blocks
- Formulas
- Page markers

**Concept Coverage:**
- Duration: Covered in chunks
- Sharpe Ratio: Covered in chunks
- Black-Scholes: Covered in chunks
- Portfolio: Covered in chunks
- Risk: Covered in chunks

**Chunk Type Distribution:**
- Code chunks: Multiple
- Formula chunks: Multiple
- Example chunks: Multiple
- Definition chunks: Multiple
- Text chunks: Multiple

**Pros:**
- Keeps related content together
- Concept-aware
- Variable chunk sizes
- Good for definitions/examples

**Cons:**
- Most complex
- Slowest processing
- Requires pattern matching
- May miss some boundaries

**Use Case**: Best for concept-based retrieval (definitions, examples)

**Example:**
```
Chunk 1: "## Duration\n\n### Definition\nDuration measures bond price sensitivity...\n\n### Formula\n$$D = \\frac{1}{P} \\sum...$$\n\n### Example\n```matlab\n>> duration = calculate...\n```"
```

---

## Metrics & Validation

### Chunk Size Validation
- **Min size**: 100 characters
- **Max size**: 2000 characters
- **Target**: 1000 characters
- **Overlap**: 200 characters

### Token Counting
- Uses `tiktoken` (GPT-3.5/4 encoding)
- 1 token ≈ 4 characters (approximate)
- Accurate for embedding model compatibility

### Processing Speed
All strategies are fast enough for production use:
- RecursiveCharacter: Instant
- MarkdownHeader: 0.01s
- CodeAware: 0.00s
- SemanticSection: 0.00s

---

## Final Recommendations

### For AURELIA RAG System: **CodeAware** ⭐

**Justification:**
1. ✅ **Best for Financial Toolbox**: Contains MATLAB code examples
2. ✅ **Consistent chunk sizes**: 776 chars (optimal)
3. ✅ **Optimal token count**: 285 tokens (good for embeddings)
4. ✅ **Code preservation**: 100% (no broken code blocks)
5. ✅ **Context preservation**: Includes surrounding text
6. ✅ **Fast processing**: 17,344 chunks/sec

### Alternative Strategies:

**RecursiveCharacter** - Use for:
- General-purpose queries
- Fast retrieval
- Consistent chunk sizes

**MarkdownHeader** - Use for:
- Structure-heavy queries
- Section-based retrieval
- Hierarchical navigation

**SemanticSection** - Use for:
- Concept-based queries
- Definition retrieval
- Example-based learning

---

## Implementation

### Recommended Configuration
```python
from chunkers.code_aware_chunker import CodeAwareChunker

chunker = CodeAwareChunker(
    chunk_size=1000,
    chunk_overlap=200,
    max_code_chunk_size=2000,
    include_surrounding_context=True,
    context_paragraphs=2
)

chunks = chunker.chunk(text, metadata={'source': 'fintbx.pdf'})
```

### Chunk Structure
```python
{
    'chunk_id': 'code_1_a1b2c3d4',
    'content': 'Chunk text with code...',
    'metadata': {
        'page': 1,
        'section_title': 'Introduction',
        'has_code': True,
        'chunk_index': 0,
        'strategy': 'CodeAware',
        'total_chunks': 72
    },
    'embeddings': None,
    'token_count': 285
}
```

---

## Files Generated

```
outputs/
├── chunking_tests/
│   ├── recursive_benchmark.json
│   ├── recursive_example_chunks.json
│   ├── markdown_header_example_chunks.json
│   ├── markdown_header_hierarchy_stats.json
│   ├── markdown_header_level_tests.json
│   ├── code_aware_example_chunks.json
│   ├── code_aware_validation.json
│   ├── semantic_section_example_chunks.json
│   └── semantic_concept_coverage.json
└── chunking_evaluation/
    ├── chunking_evaluation.json
    └── chunking_evaluation.md
```

---

## Conclusion

After comprehensive testing and evaluation, **CodeAwareChunker** is recommended for the AURELIA RAG system because:

1. ✅ Best balance of consistency and context
2. ✅ Preserves MATLAB code examples completely
3. ✅ Optimal token count for embeddings (285 avg)
4. ✅ Fast processing (17,344 chunks/sec)
5. ✅ 100% code preservation rate
6. ✅ Includes surrounding context for better retrieval

**Next Steps:**
1. Generate embeddings for chunks
2. Store in vector database (Pinecone/ChromaDB)
3. Implement RAG retrieval
4. Test with sample queries

