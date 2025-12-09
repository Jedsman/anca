"""
File Reader Tool
Reads markdown files from the articles directory
"""
from crewai.tools import BaseTool
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileReaderTool(BaseTool):
    name: str = "FileReaderTool"
    description: str = (
        "Reads content from markdown files in the 'articles' directory. "
        "Provide the filename to read."
    )

    def _run(self, filename: str) -> str:
        """
        Read a file from the articles directory.
        
        Args:
            filename: Name of the file to read (e.g., 'my-article.md')
            
        Returns:
            File content as string
        """
        try:
            base_dir = Path(__file__).parent.parent
            articles_dir = base_dir / 'articles'
            
            # Robustness: Strip directory if provided (e.g., if agent sends "articles/file.md")
            clean_filename = Path(filename).name
            file_path = articles_dir / clean_filename
            
            if not file_path.exists():
                # Try adding .md extension if it's missing and file wasn't found
                if not clean_filename.lower().endswith('.md'):
                    alt_path = articles_dir / f"{clean_filename}.md"
                    if alt_path.exists():
                        file_path = alt_path
                        logger.info(f"files found with added .md extension: {file_path}")
            
            if not file_path.exists():
                return f"❌ File not found: {filename} (checked {file_path})"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Read {len(content)} characters from {file_path}")
            return content
            
        except Exception as e:
            error_msg = f"❌ Error reading file '{filename}': {e}"
            logger.error(error_msg)
            return error_msg
