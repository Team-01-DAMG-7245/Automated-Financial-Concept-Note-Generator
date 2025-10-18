"""
Embed Hybrid Chunks Script
Embeds chunks from the hybrid chunking strategy using OpenAI's text-embedding-3-large
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk
from embeddings.embedder import Embedder
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_chunks_from_json(file_path: Path) -> List[Chunk]:
    """Load chunks from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    chunks = []
    for item in data:
        chunk = Chunk(
            content=item['content'],
            metadata=item['metadata'],
            embeddings=item.get('embeddings')
        )
        chunks.append(chunk)
    
    return chunks


def save_chunks_with_embeddings(chunks: List[Chunk], output_path: Path):
    """Save chunks with embeddings to JSON"""
    data = []
    for chunk in chunks:
        data.append({
            'content': chunk.content,
            'metadata': chunk.metadata,
            'embeddings': chunk.embeddings
        })
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(chunks)} chunks with embeddings to {output_path}")


def main():
    """Main function to embed hybrid chunks"""
    
    # Paths
    input_file = Path('outputs/chunks/chunks_hybrid.json')
    output_file = Path('outputs/chunks/chunks_hybrid_embedded.json')
    cache_dir = Path('outputs/embeddings_cache')
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.info("Please run the hybrid chunker first to generate chunks")
        return
    
    # Load chunks
    logger.info(f"Loading chunks from {input_file}")
    chunks = load_chunks_from_json(input_file)
    logger.info(f"Loaded {len(chunks)} chunks")
    
    # Initialize embedder
    logger.info("Initializing embedder...")
    embedder = Embedder(
        model="text-embedding-3-large",
        batch_size=100,
        max_retries=3,
        retry_delay=1.0,
        cache_dir=str(cache_dir),
        dimension=3072
    )
    
    # Estimate cost
    cost = embedder.estimate_cost(chunks)
    logger.info(f"Estimated cost for {len(chunks)} chunks: ${cost:.4f}")
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    print("EMBEDDING CONFIRMATION")
    print("=" * 80)
    print(f"Chunks to embed: {len(chunks)}")
    print(f"Estimated cost: ${cost:.4f}")
    print(f"Model: text-embedding-3-large")
    print(f"Dimension: 3072")
    print(f"Batch size: 100")
    print("=" * 80)
    
    response = input("\nProceed with embedding? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        logger.info("Embedding cancelled by user")
        return
    
    # Embed chunks
    logger.info("Starting embedding process...")
    embedded_chunks = embedder.embed_chunks(chunks, show_progress=True)
    
    # Validate embeddings
    logger.info("Validating embeddings...")
    is_valid = embedder.validate_embeddings(embedded_chunks)
    
    if not is_valid:
        logger.error("Validation failed! Some chunks have invalid embeddings")
        return
    
    logger.info("Validation passed! All chunks have valid embeddings")
    
    # Save embedded chunks
    logger.info(f"Saving embedded chunks to {output_file}")
    save_chunks_with_embeddings(embedded_chunks, output_file)
    
    # Save statistics
    stats = embedder.get_stats()
    stats_file = Path('outputs/embeddings_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Statistics saved to {stats_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("EMBEDDING COMPLETE")
    print("=" * 80)
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Embedded: {stats['embedded_chunks']}")
    print(f"Cached: {stats['cached_chunks']}")
    print(f"Failed: {stats['failed_chunks']}")
    print(f"Total tokens: {stats['total_tokens']:,}")
    print(f"Total cost: ${stats['total_cost']:.4f}")
    print(f"Total time: {stats['total_time']:.2f}s")
    print(f"API calls: {stats['api_calls']}")
    print(f"Retries: {stats['retries']}")
    print("=" * 80)
    print(f"\nEmbedded chunks saved to: {output_file}")
    print(f"Statistics saved to: {stats_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()

