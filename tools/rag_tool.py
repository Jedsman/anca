"""
RAG Tool for ANCA
Handles document storage and retrieval using ChromaDB
"""
from crewai.tools import BaseTool
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field
import chromadb
from chromadb.config import Settings
from pathlib import Path
import logging
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGToolSchema(BaseModel):
    """Input for RAGTool."""
    action: str = Field(..., description="Action to perform: 'ingest' or 'retrieve'.")
    url: Optional[str] = Field(None, description="URL to ingest (required for 'ingest' action).")
    query: Optional[str] = Field(None, description="Query string (required for 'retrieve' action).")

class RAGTool(BaseTool):
    name: str = "RAGTool"
    description: str = (
        "Stores and retrieves relevant content. "
        "Use 'ingest' with a 'url' to store content from a scraped site. "
        "Use 'retrieve' with a 'query' to find relevant information from stored documents."
    )
    args_schema: Type[BaseModel] = RAGToolSchema
    
    # ChromaDB configuration
    chroma_dir: str = ".chroma"
    collection_name: str = "anca_documents"
    
    # Scraper Cache configuration (must match ScraperTool)
    scraper_cache_dir: str = ".cache/scraper"
    
    # Internal state
    _client: Optional[chromadb.Client] = None
    _collection: Optional[chromadb.Collection] = None
    _ingested_urls: set = set()  # Track URLs already ingested this session

    def __init__(self, **data):
        super().__init__(**data)
        self._ingested_urls = set()  # Initialize per instance
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent client
            chroma_path = Path(self.chroma_dir)
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "ANCA scraped content storage"}
            )
            
            logger.info(f"ChromaDB initialized: {self._collection.count()} documents")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def clear_collection(self):
        """Clear all documents from the collection and reset ingested URLs tracker."""
        try:
            # Safely clear by deleting all documents instead of dropping the collection
            # This prevents "Collection does not exist" errors due to stale references
            existing_docs = self._collection.get()
            if existing_docs and existing_docs['ids']:
                self._collection.delete(ids=existing_docs['ids'])
                logger.info(f"Deleted {len(existing_docs['ids'])} documents from collection")
            
            self._ingested_urls.clear()
            logger.info("ChromaDB collection cleared (documents removed)")
            return "✅ Collection cleared successfully"
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return f"❌ Error clearing collection: {e}"

    def _generate_doc_id(self, url: str, chunk_index: int) -> str:
        """Generate unique document ID."""
        content = f"{url}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
        
    def _get_cached_chunks(self, url: str) -> List[Dict[str, Any]]:
        """Retrieve chunks from ScraperTool cache."""
        try:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            cache_file = Path(self.scraper_cache_dir) / f"{cache_key}.json"
            
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('chunks', [])
            return []
        except Exception as e:
            logger.error(f"Error reading cache for {url}: {e}")
            return []
    
    def ingest(self, url: str) -> str:
        """
        Ingest document chunks from ScraperTool cache into ChromaDB.
        
        Args:
            url: URL of the scraped page
            
        Returns:
            Success message
        """
        try:
            if not url:
                return "❌ Error: URL is required for ingestion."

            # Skip if already ingested this session
            if url in self._ingested_urls:
                logger.info(f"⏭️ Skipping already ingested URL: {url}")
                return f"⏭️ URL already ingested this session: {url}"

            chunks = self._get_cached_chunks(url)
            
            if not chunks:
                return f"⚠️ No cached content found for {url}. Please scrape the URL first using ScraperTool."
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                
                # Generate unique ID
                url_meta = metadata.get('url', url)
                chunk_idx = metadata.get('chunk_index', 0)
                doc_id = self._generate_doc_id(url_meta, chunk_idx)
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Add to collection
            if documents:
                self._collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                self._ingested_urls.add(url)  # Mark as ingested
                logger.info(f"Ingested {len(documents)} chunks from {url} into ChromaDB")
                return f"✅ Successfully ingested {len(documents)} chunks from {url}"
            else:
                return f"⚠️ Found 0 chunks for {url}."
            
        except Exception as e:
            error_msg = f"❌ Error ingesting documents: {e}"
            logger.error(error_msg)
            return error_msg
    
    def retrieve(self, query: str, n_results: int = 5) -> str:
        """
        Retrieve relevant content based on query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            Formatted string with retrieved content
        """
        try:
            if not query:
                return "❌ Error: Query is required for retrieval."

            # Query the collection
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant content found."
            
            # Format results
            output_parts = [f"# Retrieved Content for: {query}", ""]
            
            for i, (doc, metadata) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0]
            )):
                output_parts.append(f"## Result {i+1}")
                output_parts.append(f"Source: {metadata.get('url', 'Unknown')}")
                output_parts.append(f"Chunk: {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks', '?')}")
                output_parts.append("")
                output_parts.append(doc)
                output_parts.append("")
            
            logger.info(f"Retrieved {len(results['documents'][0])} results for query: {query}")
            return "\n".join(output_parts)
            
        except Exception as e:
            error_msg = f"❌ Error retrieving content: {e}"
            logger.error(error_msg)
            return error_msg
    
    def _run(self, action: str, url: Optional[str] = None, query: Optional[str] = None, **kwargs) -> str:
        """
        Main entry point for the tool.
        """
        if action == "ingest":
            return self.ingest(url)
        elif action == "retrieve":
            return self.retrieve(query)
        else:
            return f"❌ Unknown action: {action}. Use 'ingest' or 'retrieve'."
