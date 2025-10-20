#!/usr/bin/env python3
"""
Chunking Strategy Evaluator
Comprehensive comparison of all chunking strategies
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk, compare_chunking_strategies, validate_chunk_sizes
from chunkers.recursive_chunker import RecursiveChunker, benchmark_configurations
from chunkers.markdown_header_chunker import MarkdownHeaderChunker, test_hierarchy_preservation
from chunkers.code_aware_chunker import CodeAwareChunker, validate_code_blocks
from chunkers.semantic_section_chunker import SemanticSectionChunker, test_financial_concepts


class ChunkingEvaluator:
    """Evaluates and compares chunking strategies"""
    
    def __init__(self):
        self.results = {}
    
    def evaluate_strategy(
        self,
        name: str,
        text: str,
        strategy_class,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate a single chunking strategy
        
        Returns:
            Dictionary with evaluation results
        """
        start_time = time.time()
        
        # Create strategy instance
        strategy = strategy_class(**kwargs)
        
        # Apply chunking
        chunks = strategy.chunk(text, metadata={'source': 'fintbx.pdf'})
        
        elapsed_time = time.time() - start_time
        
        # Calculate metrics
        chunk_sizes = [len(c.content) for c in chunks]
        token_counts = [c.get_token_count() for c in chunks]
        
        # Validation
        validation = validate_chunk_sizes(chunks)
        
        # Analysis
        analysis = {
            'strategy_name': name,
            'total_chunks': len(chunks),
            'avg_chunk_size': statistics.mean(chunk_sizes),
            'median_chunk_size': statistics.median(chunk_sizes),
            'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
            'std_chunk_size': statistics.stdev(chunk_sizes) if len(chunk_sizes) > 1 else 0,
            'avg_tokens': statistics.mean(token_counts),
            'median_tokens': statistics.median(token_counts),
            'processing_time': elapsed_time,
            'chunks_per_second': len(chunks) / elapsed_time if elapsed_time > 0 else 0,
            'validation': validation,
            'metadata': strategy.get_chunk_metadata()
        }
        
        # Strategy-specific metrics
        if name == 'recursive':
            code_test = validate_code_blocks(chunks)
            analysis['code_preservation'] = code_test
        
        elif name == 'markdown':
            hierarchy_stats = test_hierarchy_preservation(text)
            analysis['hierarchy_preservation'] = hierarchy_stats
        
        elif name == 'code_aware':
            code_validation = validate_code_blocks(chunks)
            analysis['code_validation'] = code_validation
        
        elif name == 'semantic':
            concepts = ['Duration', 'Sharpe Ratio', 'Black-Scholes', 'Portfolio', 'Risk']
            concept_coverage = test_financial_concepts(text, concepts)
            analysis['concept_coverage'] = {
                concept: coverage['total_chunks'] 
                for concept, coverage in concept_coverage.items()
            }
        
        return analysis
    
    def compare_all_strategies(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Compare all chunking strategies
        
        Returns:
            Dictionary with comparison results
        """
        strategies = {
            'recursive': (RecursiveChunker, {}),
            'markdown': (MarkdownHeaderChunker, {}),
            'code_aware': (CodeAwareChunker, {}),
            'semantic': (SemanticSectionChunker, {})
        }
        
        results = {}
        
        for name, (strategy_class, kwargs) in strategies.items():
            print(f"\nEvaluating {name} strategy...")
            try:
                evaluation = self.evaluate_strategy(
                    name,
                    text,
                    strategy_class,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
                results[name] = evaluation
                print(f"  [OK] {evaluation['total_chunks']} chunks in {evaluation['processing_time']:.2f}s")
            except Exception as e:
                print(f"  [ERROR] {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    def generate_comparison_report(
        self,
        results: Dict[str, Any],
        output_dir: Path
    ):
        """Generate comprehensive comparison report"""
        
        # Create report
        report = {
            'summary': {
                'total_strategies': len([r for r in results.values() if 'error' not in r]),
                'strategies_tested': list(results.keys())
            },
            'comparison': {},
            'recommendations': [],
            'pros_cons': {}
        }
        
        # Compare metrics
        metrics = ['total_chunks', 'avg_chunk_size', 'avg_tokens', 'processing_time', 'chunks_per_second']
        
        for metric in metrics:
            report['comparison'][metric] = {}
            values = []
            
            for strategy_name, result in results.items():
                if 'error' not in result and metric in result:
                    value = result[metric]
                    report['comparison'][metric][strategy_name] = value
                    values.append((strategy_name, value))
            
            if values:
                # Find best and worst
                if metric in ['processing_time']:
                    # Lower is better
                    best = min(values, key=lambda x: x[1])
                    worst = max(values, key=lambda x: x[1])
                else:
                    # Higher is better (or depends on context)
                    if metric in ['total_chunks', 'chunks_per_second']:
                        best = max(values, key=lambda x: x[1])
                        worst = min(values, key=lambda x: x[1])
                    else:
                        # For avg_chunk_size and avg_tokens, closer to target is better
                        target = 1000 if metric == 'avg_chunk_size' else 300
                        best = min(values, key=lambda x: abs(x[1] - target))
                        worst = max(values, key=lambda x: abs(x[1] - target))
                
                report['comparison'][metric]['best'] = best[0]
                report['comparison'][metric]['worst'] = worst[0]
        
        # Generate pros and cons
        report['pros_cons'] = {
            'recursive': {
                'pros': [
                    'Most consistent chunk sizes',
                    'Fastest processing',
                    '100% valid chunks',
                    'Good for general-purpose text'
                ],
                'cons': [
                    'May split code blocks',
                    'No semantic awareness',
                    'Ignores document structure'
                ]
            },
            'markdown': {
                'pros': [
                    'Preserves document hierarchy',
                    'Maintains section context',
                    'Good for structured documents',
                    'Rich metadata'
                ],
                'cons': [
                    'Variable chunk sizes',
                    'Some chunks too large',
                    'Slower than recursive',
                    'Requires markdown format'
                ]
            },
            'code_aware': {
                'pros': [
                    'Preserves code blocks',
                    'Includes surrounding context',
                    'Good for technical documents',
                    'No broken code'
                ],
                'cons': [
                    'Slower processing',
                    'More complex',
                    'May create large chunks',
                    'Requires code detection'
                ]
            },
            'semantic': {
                'pros': [
                    'Keeps related content together',
                    'Concept-aware',
                    'Variable chunk sizes',
                    'Good for definitions/examples'
                ],
                'cons': [
                    'Most complex',
                    'Slowest processing',
                    'Requires pattern matching',
                    'May miss some boundaries'
                ]
            }
        }
        
        # Generate recommendations
        if 'recursive' in results and 'error' not in results['recursive']:
            if results['recursive']['validation']['valid_chunks'] == results['recursive']['total_chunks']:
                report['recommendations'].append(
                    "RecursiveCharacter: Best for general-purpose RAG with consistent chunk sizes"
                )
        
        if 'markdown' in results and 'error' not in results['markdown']:
            hierarchy = results['markdown'].get('hierarchy_preservation', {})
            if hierarchy.get('chunks_with_headers', 0) > hierarchy.get('chunks_without_headers', 0):
                report['recommendations'].append(
                    "MarkdownHeader: Best for structured documents with clear hierarchies"
                )
        
        if 'code_aware' in results and 'error' not in results['code_aware']:
            code_val = results['code_aware'].get('code_validation', {})
            if code_val.get('validation_passed', False):
                report['recommendations'].append(
                    "CodeAware: Best for technical documents with code examples"
                )
        
        if 'semantic' in results and 'error' not in results['semantic']:
            concept_cov = results['semantic'].get('concept_coverage', {})
            if sum(concept_cov.values()) > 0:
                report['recommendations'].append(
                    "SemanticSection: Best for concept-based retrieval (definitions, examples)"
                )
        
        # Save report
        with open(output_dir / "chunking_evaluation.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate markdown report
        self.generate_markdown_report(report, output_dir)
        
        return report
    
    def generate_markdown_report(self, report: Dict[str, Any], output_dir: Path):
        """Generate markdown report"""
        
        lines = []
        lines.append("# Chunking Strategy Evaluation Report\n")
        lines.append("## Summary\n")
        lines.append(f"- **Total Strategies**: {report['summary']['total_strategies']}\n")
        lines.append(f"- **Strategies Tested**: {', '.join(report['summary']['strategies_tested'])}\n")
        
        # Comparison table
        lines.append("\n## Strategy Comparison\n")
        lines.append("| Strategy | Chunks | Avg Size | Avg Tokens | Processing Time | Chunks/sec |\n")
        lines.append("|----------|--------|----------|------------|-----------------|------------|\n")
        
        for strategy_name in report['summary']['strategies_tested']:
            if strategy_name in report['comparison']['total_chunks']:
                chunks = report['comparison']['total_chunks'][strategy_name]
                size = report['comparison']['avg_chunk_size'][strategy_name]
                tokens = report['comparison']['avg_tokens'][strategy_name]
                time_val = report['comparison']['processing_time'][strategy_name]
                rate = report['comparison']['chunks_per_second'][strategy_name]
                
                lines.append(f"| {strategy_name} | {chunks} | {size:.0f} | {tokens:.0f} | {time_val:.2f}s | {rate:.1f} |\n")
        
        # Pros and Cons
        lines.append("\n## Pros and Cons\n")
        for strategy_name, pros_cons in report['pros_cons'].items():
            lines.append(f"### {strategy_name}\n")
            lines.append("**Pros:**\n")
            for pro in pros_cons['pros']:
                lines.append(f"- {pro}\n")
            lines.append("\n**Cons:**\n")
            for con in pros_cons['cons']:
                lines.append(f"- {con}\n")
            lines.append("\n")
        
        # Recommendations
        lines.append("## Recommendations\n")
        for i, recommendation in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {recommendation}\n")
        
        # Write report
        with open(output_dir / "chunking_evaluation.md", 'w', encoding='utf-8') as f:
            f.write(''.join(lines))


def main():
    """Run comprehensive chunking evaluation"""
    
    # Load sample text
    markdown_file = Path("outputs/fintbx_complete.md")
    if not markdown_file.exists():
        print("[ERROR] Markdown file not found. Run markdown_generator.py first.")
        return
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Limit text for testing
    text = text[:50000]  # First ~50k characters
    
    print("=" * 70)
    print("Chunking Strategy Evaluator")
    print("=" * 70)
    print(f"Text size: {len(text):,} characters")
    print(f"Estimated tokens: {len(text) // 4:,}")
    print("=" * 70)
    
    # Create evaluator
    evaluator = ChunkingEvaluator()
    
    # Compare all strategies
    results = evaluator.compare_all_strategies(
        text,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Generate report
    output_dir = Path("outputs/chunking_evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating comparison report...")
    report = evaluator.generate_comparison_report(results, output_dir)
    
    # Print summary
    print("\n" + "=" * 70)
    print("[SUCCESS] Chunking Evaluation Complete!")
    print("=" * 70)
    print("\nTop Strategy by Metric:")
    
    for metric in ['total_chunks', 'avg_tokens', 'processing_time']:
        if metric in report['comparison']:
            best = report['comparison'][metric].get('best', 'N/A')
            print(f"  {metric}: {best}")
    
    print("\nRecommendations:")
    for i, recommendation in enumerate(report['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    print(f"\nReports saved to: {output_dir}")
    print("  - chunking_evaluation.json")
    print("  - chunking_evaluation.md")
    print("=" * 70)


if __name__ == "__main__":
    main()

