"""
Test script for Wikipedia fallback service
"""
import asyncio
import logging
from app.services.wikipedia_fallback import WikipediaFallbackService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_fetch_content():
    """Test fetching Wikipedia content"""
    print("=" * 60)
    print("Testing Wikipedia Content Fetching")
    print("=" * 60)
    print()
    
    service = WikipediaFallbackService()
    
    # Test concepts
    concepts = [
        "revenue recognition",
        "depreciation",
        "cash flow",
        "financial reporting"
    ]
    
    for concept in concepts:
        print(f"Fetching: '{concept}'")
        try:
            result = await service.fetch_wikipedia_content(concept)
            
            if result:
                print(f"  ✅ Success!")
                print(f"  Title: {result['title']}")
                print(f"  URL: {result['url']}")
                print(f"  Total chunks: {result['total_chunks']}")
                print(f"  Content length: {len(result['content'])} characters")
                print(f"  First chunk preview: {result['chunks'][0][:100]}...")
            else:
                print(f"  ⚠️  No content found")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()


async def test_get_fallback_chunks():
    """Test getting fallback chunks"""
    print("=" * 60)
    print("Testing Fallback Chunks Retrieval")
    print("=" * 60)
    print()
    
    service = WikipediaFallbackService()
    
    concept = "revenue recognition"
    print(f"Getting fallback chunks for: '{concept}'")
    print()
    
    try:
        chunks = await service.get_fallback_chunks(concept, top_k=3)
        
        if chunks:
            print(f"✅ Retrieved {len(chunks)} chunks:")
            print()
            
            for i, chunk in enumerate(chunks, 1):
                print(f"Chunk {i}:")
                print(f"  Score: {chunk.score}")
                print(f"  Source: {chunk.metadata.get('source')}")
                print(f"  Title: {chunk.metadata.get('title')}")
                print(f"  URL: {chunk.metadata.get('url')}")
                print(f"  Content: {chunk.content[:150]}...")
                print()
        else:
            print("⚠️  No chunks retrieved")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()


async def test_rate_limiting():
    """Test rate limiting"""
    print("=" * 60)
    print("Testing Rate Limiting")
    print("=" * 60)
    print()
    
    service = WikipediaFallbackService()
    
    import time
    
    concepts = ["revenue", "depreciation", "cash flow"]
    
    print("Making 3 consecutive requests with rate limiting...")
    print()
    
    for i, concept in enumerate(concepts, 1):
        start_time = time.time()
        print(f"Request {i}: '{concept}'")
        
        result = await service.fetch_wikipedia_content(concept)
        
        elapsed = time.time() - start_time
        
        if result:
            print(f"  ✅ Success in {elapsed:.2f}s")
        else:
            print(f"  ⚠️  No content in {elapsed:.2f}s")
        
        print()


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Wikipedia Fallback Service Tests" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Test 1: Fetch content
    await test_fetch_content()
    
    # Test 2: Get fallback chunks
    await test_get_fallback_chunks()
    
    # Test 3: Rate limiting
    await test_rate_limiting()
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())

