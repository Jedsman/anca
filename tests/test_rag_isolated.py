"""
Isolated test for RAG Tool
Tests document ingestion and retrieval
"""
from tools.rag_tool import RAGTool
import time

def test_rag():
    print("=" * 60)
    print("Testing RAG Tool in isolation")
    print("=" * 60)
    
    rag = RAGTool()
    
    # Test data - sample chunks
    test_chunks = [
        {
            'content': 'French press coffee requires a coarse grind. The grind size is crucial for proper extraction.',
            'metadata': {
                'url': 'https://example.com/coffee',
                'chunk_index': 0,
                'total_chunks': 3,
                'scraped_at': '2025-12-08T14:00:00'
            }
        },
        {
            'content': 'Water temperature should be between 195-205°F for optimal brewing. Too hot will over-extract.',
            'metadata': {
                'url': 'https://example.com/coffee',
                'chunk_index': 1,
                'total_chunks': 3,
                'scraped_at': '2025-12-08T14:00:00'
            }
        },
        {
            'content': 'Steep time for french press is typically 4 minutes. Longer steeping can make coffee bitter.',
            'metadata': {
                'url': 'https://example.com/coffee',
                'chunk_index': 2,
                'total_chunks': 3,
                'scraped_at': '2025-12-08T14:00:00'
            }
        }
    ]
    
    # Test ingestion
    print("\n📥 Testing ingestion...")
    result = rag.ingest(test_chunks)
    print(f"Result: {result}")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    queries = [
        "What grind size for french press?",
        "What temperature for brewing?",
        "How long to steep?"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        result = rag.retrieve(query, n_results=2)
        print(result[:300] + "..." if len(result) > 300 else result)
    
    print("\n✅ RAG tool test complete!")

if __name__ == "__main__":
    test_rag()
