"""
Pytest configuration and fixtures for ANCA tests
"""
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_article_content():
    """Sample article content for testing"""
    return """# Test Article

This is a test article with some content.

## Section 1
Some information here.

## Section 2
More information here.
"""


@pytest.fixture
def sample_url():
    """Sample URL for testing"""
    return "https://example.com/test-page"


@pytest.fixture
def mock_scraped_chunks():
    """Mock scraped content chunks"""
    return [
        {
            "content": "This is the first chunk of content.",
            "metadata": {
                "url": "https://example.com/test",
                "chunk_index": 0,
                "total_chunks": 2,
                "scraped_at": "2025-12-09T10:00:00"
            }
        },
        {
            "content": "This is the second chunk of content.",
            "metadata": {
                "url": "https://example.com/test",
                "chunk_index": 1,
                "total_chunks": 2,
                "scraped_at": "2025-12-09T10:00:00"
            }
        }
    ]


@pytest.fixture
def mock_rag_collection(monkeypatch):
    """Mock ChromaDB collection for testing"""
    class MockCollection:
        def __init__(self):
            self._documents = []
            self._metadatas = []
            self._ids = []

        def add(self, documents, metadatas, ids):
            self._documents.extend(documents)
            self._metadatas.extend(metadatas)
            self._ids.extend(ids)

        def query(self, query_texts, n_results=5):
            # Return mock results
            return {
                'documents': [[doc for doc in self._documents[:n_results]]],
                'metadatas': [[meta for meta in self._metadatas[:n_results]]],
                'ids': [[id for id in self._ids[:n_results]]]
            }

        def count(self):
            return len(self._documents)

    return MockCollection()


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    """Setup test environment variables"""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")  # Reduce log noise in tests

    # Set test directories
    test_articles_dir = tmp_path / "articles"
    test_articles_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("ARTICLES_DIR", str(test_articles_dir))

    return {
        "articles_dir": test_articles_dir,
        "tmp_path": tmp_path
    }
