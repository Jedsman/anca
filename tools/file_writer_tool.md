# FileWriterTool

**Stage:** 1  
**Type:** File operations

## Purpose
Writes content to markdown files in the `articles/` directory.

## Features
- **Auto directory creation** - Creates `articles/` if needed
- **Absolute path handling** - Works from any directory
- **Error logging** - Detailed error messages
- **UTF-8 encoding** - Proper character support

## Usage
```python
from tools import FileWriterTool

writer = FileWriterTool()
result = writer._run(
    content="# My Article\n\nContent here...",
    filename="my-article.md"
)
# Returns: "✅ Successfully wrote article to: /path/to/articles/my-article.md"
```

## Output
Files saved to `articles/` directory with specified filename.
