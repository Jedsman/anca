"""
Isolated test for FileWriterTool
Tests file writing functionality without agents
"""
from tools.file_writer_tool import FileWriterTool
from pathlib import Path
import time

def test_file_writer():
    print("=" * 60)
    print("Testing FileWriterTool in isolation")
    print("=" * 60)
    
    writer = FileWriterTool()
    
    # Test content
    test_content = """# Test Article

This is a test article created at {}.

## Features
- Automatic directory creation
- Error handling
- Logging support
""".format(time.strftime("%Y-%m-%d %H:%M:%S"))
    
    test_filename = f"test-isolated-{int(time.time())}.md"
    
    print(f"\n📝 Writing test file: {test_filename}")
    print(f"📄 Content length: {len(test_content)} chars")
    
    result = writer._run(content=test_content, filename=test_filename)
    
    print(f"\n✅ Result: {result}")
    
    # Verify file exists
    base_dir = Path(__file__).parent.parent
    articles_dir = base_dir / 'articles'
    test_file = articles_dir / test_filename
    
    if test_file.exists():
        print(f"✅ File exists: {test_file}")
        print(f"📊 File size: {test_file.stat().st_size} bytes")
        
        # Read back content
        with open(test_file, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        print(f"✅ Content matches: {read_content == test_content}")
    else:
        print(f"❌ File not found: {test_file}")
    
    return result

if __name__ == "__main__":
    test_file_writer()
