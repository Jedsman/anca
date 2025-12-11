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
            
            # Strategy 1: Try exact match
            if file_path.exists():
                logger.info(f"Found file (exact match): {file_path}")
            else:
                # Strategy 2: Try with .md extension if missing
                if not clean_filename.lower().endswith('.md'):
                    alt_path = articles_dir / f"{clean_filename}.md"
                    if alt_path.exists():
                        file_path = alt_path
                        logger.info(f"Found file with added .md extension: {file_path}")
                
                # Strategy 3: Try different slug variations (handle hyphen inconsistencies)
                if not file_path.exists():
                    base_name = clean_filename.replace('.md', '').replace('.MD', '')
                    variations = [
                        base_name.replace('-', ''),  # homebrew-coffee → homebrewcoffee
                        base_name.replace(' ', '-'),  # homebrew coffee → homebrew-coffee
                        base_name.replace(' ', ''),   # homebrew coffee → homebrewcoffee
                    ]
                    
                    for variation in variations:
                        test_path = articles_dir / f"{variation}.md"
                        if test_path.exists():
                            file_path = test_path
                            logger.info(f"Found file with slug variation: {file_path} (from {filename})")
                            break
                
                # Strategy 4: Fuzzy search - find any file containing the base topic
                if not file_path.exists():
                    topic_words = base_name.lower().replace('-', ' ').split()
                    if topic_words:
                        for article_file in articles_dir.glob('*.md'):
                            article_name = article_file.stem.lower()
                            # Check if all topic words appear in the filename
                            if all(word in article_name for word in topic_words):
                                file_path = article_file
                                logger.info(f"Found file via fuzzy match: {file_path} (from {filename})")
                                break
            
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
