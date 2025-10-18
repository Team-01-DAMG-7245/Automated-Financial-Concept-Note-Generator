#!/usr/bin/env python3
"""
Chunking Pipeline for AURELIA
Applies multiple chunking strategies to the parsed PDF data
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import argparse

from chunkers.base_chunker import (
    RecursiveCharacterChunker,
    MarkdownHeaderChunker,
    SectionAwareChunker,
    CodeAwareChunker,
    compare_chunking_strategies,
    validate_chunk_sizes,
    analyze_chunking_strategy
)


def load_markdown_content(markdown_file: Path) -> str:
    """Load markdown content from file"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        return f.read()


def apply_chunking_strategy(
    text: str,
    strategy_name: str,
    chunk_size: int,
    chunk_overlap: int,
    metadata: Dict[str, Any] = None
) -> List[Any]:
    """Apply a specific chunking strategy"""
    
    # Select strategy
    if strategy_name == 'recursive':
        strategy = RecursiveCharacterChunker(chunk_size, chunk_overlap)
    elif strategy_name == 'markdown':
        strategy = MarkdownHeaderChunker(chunk_size, chunk_overlap)
    elif strategy_name == 'section':
        strategy = SectionAwareChunker(chunk_size, chunk_overlap)
    elif strategy_name == 'code':
        strategy = CodeAwareChunker(chunk_size, chunk_overlap)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    # Apply chunking
    chunks = strategy.chunk(text, metadata or {})
    
    return chunks


def save_chunks(chunks: List[Any], output_file: Path):
    """Save chunks to JSON file"""
    chunks_data = [chunk.to_dict() for chunk in chunks]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Saved {len(chunks)} chunks to {output_file}")


def generate_chunking_report(
    strategy_results: Dict[str, List[Any]],
    output_file: Path
):
    """Generate comprehensive chunking analysis report"""
    
    # Compare strategies
    comparison = compare_chunking_strategies(strategy_results)
    
    # Generate report
    report = {
        'summary': {
            'total_strategies': len(strategy_results),
            'strategies_tested': list(strategy_results.keys())
        },
        'comparison': comparison,
        'recommendations': []
    }
    
    # Add recommendations based on analysis
    for strategy_name, analysis in comparison.items():
        if analysis['avg_tokens'] < 100:
            report['recommendations'].append(
                f"{strategy_name}: Chunks too small, consider increasing chunk_size"
            )
        elif analysis['avg_tokens'] > 2000:
            report['recommendations'].append(
                f"{strategy_name}: Chunks too large, consider decreasing chunk_size"
            )
    
    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Generated chunking report: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Chunking Pipeline - Apply multiple chunking strategies"
    )
    parser.add_argument(
        "--markdown",
        default="outputs/fintbx_complete.md",
        help="Input markdown file"
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/chunks",
        help="Output directory for chunks"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size in characters"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap in characters"
    )
    parser.add_argument(
        "--strategies",
        nargs='+',
        default=['recursive', 'markdown', 'section', 'code'],
        choices=['recursive', 'markdown', 'section', 'code'],
        help="Chunking strategies to apply"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to process (for testing)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Project AURELIA - Chunking Pipeline")
    print("=" * 70)
    print(f"Input: {args.markdown}")
    print(f"Output: {args.output_dir}")
    print(f"Chunk size: {args.chunk_size}")
    print(f"Chunk overlap: {args.chunk_overlap}")
    print(f"Strategies: {', '.join(args.strategies)}")
    print("=" * 70)
    
    # Check if markdown file exists
    markdown_file = Path(args.markdown)
    if not markdown_file.exists():
        print(f"\n[ERROR] Markdown file not found: {markdown_file}")
        return
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load markdown content
    print("\nLoading markdown content...")
    text = load_markdown_content(markdown_file)
    print(f"[OK] Loaded {len(text):,} characters")
    
    # Limit text if max_pages specified
    if args.max_pages:
        # Approximate pages (assuming ~2000 chars per page)
        max_chars = args.max_pages * 2000
        text = text[:max_chars]
        print(f"[OK] Limited to {args.max_pages} pages (~{max_chars:,} characters)")
    
    # Apply each strategy
    strategy_results = {}
    
    for strategy_name in args.strategies:
        print(f"\nApplying {strategy_name} strategy...")
        
        try:
            chunks = apply_chunking_strategy(
                text,
                strategy_name,
                args.chunk_size,
                args.chunk_overlap,
                metadata={'source': 'fintbx.pdf'}
            )
            
            strategy_results[strategy_name] = chunks
            
            # Validate chunks
            validation = validate_chunk_sizes(chunks)
            analysis = analyze_chunking_strategy(chunks)
            
            print(f"  [OK] Created {validation['total_chunks']} chunks")
            print(f"  [OK] Avg size: {analysis['avg_chunk_size']:.0f} chars")
            print(f"  [OK] Avg tokens: {analysis['avg_tokens']:.0f}")
            print(f"  [OK] Valid: {validation['valid_chunks']}/{validation['total_chunks']}")
            
            # Save chunks
            output_file = output_dir / f"chunks_{strategy_name}.json"
            save_chunks(chunks, output_file)
            
        except Exception as e:
            print(f"  [ERROR] Failed to apply {strategy_name}: {e}")
            continue
    
    # Generate comparison report
    if len(strategy_results) > 1:
        print("\nGenerating comparison report...")
        report_file = output_dir / "chunking_comparison.json"
        generate_chunking_report(strategy_results, report_file)
    
    # Print final summary
    print("\n" + "=" * 70)
    print("[SUCCESS] CHUNKING PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"Strategies applied: {len(strategy_results)}")
    print(f"Output directory: {output_dir}")
    print("\nGenerated files:")
    for strategy_name in strategy_results.keys():
        print(f"  - chunks_{strategy_name}.json")
    if len(strategy_results) > 1:
        print(f"  - chunking_comparison.json")
    print("=" * 70)


if __name__ == "__main__":
    main()

