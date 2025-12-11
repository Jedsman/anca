import chromadb
from chromadb.config import Settings
from pathlib import Path

def inspect_chroma():
    chroma_dir = Path(".chroma")
    if not chroma_dir.exists():
        print(f"❌ ChromaDB directory not found at {chroma_dir}")
        return

    print(f"📂 Connecting to ChromaDB at {chroma_dir}...")
    client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )

    collection_name = "anca_documents"
    try:
        collection = client.get_collection(collection_name)
        count = collection.count()
        print(f"✅ Collection '{collection_name}' found.")
        print(f"📊 Total Documents: {count}")
        
        if count > 0:
            print("\n🔍 Peeking at first 3 documents:")
            results = collection.peek(limit=3)
            # ids, metadatas, documents
            for i, doc_id in enumerate(results['ids']):
                print(f"\n--- Document {i+1} (ID: {doc_id}) ---")
                meta = results['metadatas'][i]
                print(f"🔗 Source: {meta.get('url', 'Unknown')}")
                print(f"📑 Chunk: {meta.get('chunk_index', '?')}/{meta.get('total_chunks', '?')}")
                content_preview = results['documents'][i][:200].replace('\n', ' ')
                print(f"📝 Content: {content_preview}...")
        else:
            print("⚠️ Collection is empty.")

    except ValueError:
        print(f"❌ Collection '{collection_name}' does not exist.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_chroma()
