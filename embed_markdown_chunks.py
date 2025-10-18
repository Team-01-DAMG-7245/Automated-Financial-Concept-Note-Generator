"""Embed markdown chunks directly"""
import json
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from chunkers.base_chunker import Chunk
from embeddings.embedder import Embedder

# Load chunks
with open('outputs/chunks/chunks_markdown.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = [Chunk(content=item['content'], metadata=item['metadata'], embeddings=item.get('embeddings')) for item in data]

print(f"Loaded {len(chunks)} chunks")
print(f"Estimated cost: ${Embedder().estimate_cost(chunks):.4f}")

# Embed
embedder = Embedder(batch_size=100)
embedded = embedder.embed_chunks(chunks, show_progress=True)

# Validate
is_valid = embedder.validate_embeddings(embedded)
print(f"Validation: {'PASSED' if is_valid else 'FAILED'}")

# Save
with open('outputs/chunks/chunks_markdown_embedded.json', 'w', encoding='utf-8') as f:
    json.dump([{'content': c.content, 'metadata': c.metadata, 'embeddings': c.embeddings} for c in embedded], f, indent=2)

# Stats
stats = embedder.get_stats()
with open('outputs/embeddings_stats.json', 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2)

print("\n" + "=" * 80)
print("EMBEDDING COMPLETE")
print("=" * 80)
print(f"Total chunks: {stats['total_chunks']}")
print(f"Embedded: {stats['embedded_chunks']}")
print(f"Cached: {stats['cached_chunks']}")
print(f"Total tokens: {stats['total_tokens']:,}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Total time: {stats['total_time']:.2f}s")
print("=" * 80)

