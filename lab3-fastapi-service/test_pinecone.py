"""
Test script for Pinecone service integration
"""
import asyncio
import logging
from app.services.pinecone_service import PineconeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_pinecone_connection():
    """Test Pinecone connection"""
    print("=" * 60)
    print("Testing Pinecone Connection")
    print("=" * 60)
    print()
    
    try:
        service = PineconeService()
        
        # Test connection
        is_connected = service.test_connection()
        
        if is_connected:
            print("✅ Pinecone connection successful!")
            
            # Get index stats
            stats = service.get_index_stats()
            print(f"\nIndex Stats:")
            print(f"  - Total vectors: {stats.get('total_vector_count', 'N/A')}")
            print(f"  - Namespaces: {stats.get('namespaces', {})}")
        else:
            print("❌ Pinecone connection failed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()


async def test_query_concept():
    """Test querying for a concept"""
    print("=" * 60)
    print("Testing Concept Query")
    print("=" * 60)
    print()
    
    try:
        service = PineconeService()
        
        # Query for a concept
        concept = "revenue recognition"
        print(f"Querying for: '{concept}'")
        print()
        
        results = await service.query_similar_chunks(
            concept_query=concept,
            top_k=5
        )
        
        if results:
            print(f"✅ Found {len(results)} results:")
            print()
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"  Score: {result['similarity_score']:.3f}")
                print(f"  Section: {result['metadata']['section_title']}")
                print(f"  Page: {result['metadata']['page_number']}")
                print(f"  Source: {result['metadata']['document_source']}")
                print(f"  Text: {result['chunk_text'][:100]}...")
                print()
        else:
            print("⚠️  No results found (below threshold or empty index)")
            print("   This is expected if:")
            print("   1. Index is empty")
            print("   2. No chunks meet the similarity threshold (0.7)")
            print("   3. API keys are not configured")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()


async def test_multiple_concepts():
    """Test querying multiple concepts"""
    print("=" * 60)
    print("Testing Multiple Concepts")
    print("=" * 60)
    print()
    
    concepts = [
        "revenue recognition",
        "depreciation",
        "cash flow",
        "financial reporting"
    ]
    
    service = PineconeService()
    
    for concept in concepts:
        print(f"Querying: '{concept}'")
        
        try:
            results = await service.query_similar_chunks(
                concept_query=concept,
                top_k=3
            )
            
            if results:
                print(f"  ✅ Found {len(results)} results")
                print(f"  Top score: {results[0]['similarity_score']:.3f}")
            else:
                print(f"  ⚠️  No results")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
    
    print()


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AURELIA Pinecone Service Tests" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Test 1: Connection
    await test_pinecone_connection()
    
    # Test 2: Single query
    await test_query_concept()
    
    # Test 3: Multiple queries
    await test_multiple_concepts()
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())

