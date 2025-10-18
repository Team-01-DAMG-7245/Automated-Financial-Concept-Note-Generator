"""
Upload Embedded Chunks to Pinecone
"""

import json
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk
from storage.pinecone_store import PineconeStore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_embedded_chunks(file_path: Path) -> list:
    """Load embedded chunks from JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
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


def main():
    """Main function to upload chunks to Pinecone"""
    
    # Configuration
    embedded_file = Path('outputs/chunks/chunks_markdown_embedded.json')
    index_name = "fintbx-embeddings"
    
    # Check if file exists
    if not embedded_file.exists():
        logger.error(f"File not found: {embedded_file}")
        logger.info("Please run the embedder first to generate embeddings")
        return
    
    print("\n" + "=" * 80)
    print("UPLOAD TO PINECONE")
    print("=" * 80)
    print(f"Input file: {embedded_file}")
    print(f"Index name: {index_name}")
    print("=" * 80)
    
    # Load chunks
    logger.info(f"Loading embedded chunks from {embedded_file}")
    chunks = load_embedded_chunks(embedded_file)
    logger.info(f"Loaded {len(chunks)} chunks")
    
    # Initialize Pinecone store
    logger.info("Initializing Pinecone store...")
    store = PineconeStore(
        index_name=index_name,
        dimension=3072,
        metric="cosine",
        batch_size=100
    )
    
    # Create index
    print("\nCreating/connecting to index...")
    try:
        store.create_index(force=False)
    except Exception as e:
        logger.info("Index already exists, connecting...")
        store.connect_index()
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    print("UPLOAD CONFIRMATION")
    print("=" * 80)
    print(f"Chunks to upload: {len(chunks)}")
    print(f"Index: {index_name}")
    print(f"Dimension: 3072")
    print(f"Metric: cosine")
    print(f"Batch size: 100")
    print("=" * 80)
    
    response = input("\nProceed with upload? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        logger.info("Upload cancelled by user")
        return
    
    # Upload chunks
    logger.info("Starting upload to Pinecone...")
    upserted = store.upsert_chunks(chunks, namespace=None, show_progress=True)
    
    # Get index stats
    logger.info("Getting index statistics...")
    index_stats = store.get_index_stats()
    
    # Get storage stats
    storage_stats = store.get_stats()
    
    # Print summary
    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"Total chunks: {storage_stats['total_vectors']}")
    print(f"Upserted: {storage_stats['upserted_vectors']}")
    print(f"Failed: {storage_stats['failed_vectors']}")
    print(f"Total time: {storage_stats['total_time']:.2f}s")
    print(f"Vectors/sec: {storage_stats['upserted_vectors'] / storage_stats['total_time']:.2f}")
    print("=" * 80)
    print(f"\nIndex Statistics:")
    print(f"  Total vectors: {index_stats.get('total_vector_count', 'N/A')}")
    print(f"  Dimension: {index_stats.get('dimension', 'N/A')}")
    print(f"  Namespaces: {list(index_stats.get('namespaces', {}).keys())}")
    print("=" * 80)
    
    # Save stats
    stats_file = Path('outputs/pinecone_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump({
            'storage_stats': storage_stats,
            'index_stats': index_stats
        }, f, indent=2)
    
    logger.info(f"Statistics saved to {stats_file}")
    
    # Test query
    print("\n" + "=" * 80)
    print("TESTING QUERY")
    print("=" * 80)
    
    test_query = "What is the Sharpe Ratio?"
    print(f"Query: '{test_query}'")
    
    results = store.query_by_text(test_query, top_k=3)
    
    print(f"\nTop {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   Content: {result['metadata'].get('content', '')[:80]}...")
        print(f"   Section: {result['metadata'].get('section_title', 'N/A')}")
        print(f"   Page: {result['metadata'].get('page', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("[OK] Upload and query test complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()

