"""
Test the FileWriterTool to ensure it works correctly
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.file_writer_tool import FileWriterTool

# Initialize the tool
writer = FileWriterTool()

# Test writing a file
test_content = """# Test Article

This is a test article to verify the FileWriterTool works correctly.

## Features
- Automatic directory creation
- Error handling
- Logging support
"""

print("Testing FileWriterTool...")
print("=" * 60)

result = writer._run(content=test_content, filename="test-article.md")

print(f"\n📄 RESULT:\n{result}")

# Check if file was created
from pathlib import Path
base_dir = Path(__file__).parent
articles_dir = base_dir / 'articles'
test_file = articles_dir / 'test-article.md'

if test_file.exists():
    print(f"\n✅ File exists at: {test_file}")
    print(f"File size: {test_file.stat().st_size} bytes")
else:
    print(f"\n❌ File was not created at: {test_file}")
