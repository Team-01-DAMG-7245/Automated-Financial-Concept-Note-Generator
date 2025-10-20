"""
Simple test script for the FastAPI RAG service
"""
import asyncio
import httpx


async def test_health_check():
    """Test the health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print("Health Check Response:")
        print(response.json())
        print()


async def test_query_concept():
    """Test the query endpoint"""
    async with httpx.AsyncClient() as client:
        payload = {
            "concept_name": "revenue recognition",
            "top_k": 3
        }
        response = await client.post(
            "http://localhost:8000/api/v1/query",
            json=payload
        )
        print("Query Response:")
        print(response.json())
        print()


async def test_seed_concept():
    """Test the seed endpoint"""
    async with httpx.AsyncClient() as client:
        payload = {
            "concept_name": "revenue recognition",
            "force_refresh": False
        }
        response = await client.post(
            "http://localhost:8000/api/v1/seed",
            json=payload
        )
        print("Seed Response:")
        print(response.json())
        print()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing AURELIA FastAPI RAG Service")
    print("=" * 60)
    print()
    
    # Test health check
    await test_health_check()
    
    # Test query
    await test_query_concept()
    
    # Test seed
    await test_seed_concept()
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

