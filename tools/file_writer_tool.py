import os
import logging
from pathlib import Path
from crewai.tools import BaseTool

# Configure logging
logger = logging.getLogger(__name__)


from typing import Type
from pydantic import BaseModel, Field

class FileWriterToolSchema(BaseModel):
    """Input for FileWriterTool."""
    content: str = Field(..., description="The complete text content to write to the file.")
    filename: str = Field(..., description="The filename (e.g., 'topic-guide.md'). Do NOT include 'articles/' prefix.")

class FileWriterTool(BaseTool):
    name: str = "FileWriterTool"
    description: str = (
        "Writes content to a file in the 'articles' directory. "
        "Provide the content and filename (e.g., 'my-article.md'). "
        "The tool will automatically create the directory if needed."
    )
    args_schema: Type[BaseModel] = FileWriterToolSchema

    def _run(self, content: str, filename: str) -> str:
        """
        Write content to a file in the articles directory.
        
        Args:
            content: The content to write to the file
            filename: The name of the file (e.g., 'my-article.md')
            
        Returns:
            Success or error message
        """
        try:
            # Get the absolute path to the articles directory
            # This ensures it works regardless of current working directory
            base_dir = Path(__file__).parent.parent
            articles_dir = base_dir / 'articles'
            
            # Create the articles directory if it doesn't exist
            articles_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured articles directory exists: {articles_dir}")
            
            # Normalize filename
            clean_filename = Path(filename).name  # Remove any directory components
            if not clean_filename.lower().endswith('.md'):
                clean_filename += '.md'
                logger.info(f"Added .md extension to filename: {clean_filename}")
            
            # Create the full file path
            file_path = articles_dir / clean_filename
            
            # Write the content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully wrote {len(content)} characters to {file_path}")
            return f"✅ Successfully wrote article to: {file_path}"
            
        except Exception as e:
            error_msg = f"❌ Error writing to file '{filename}': {type(e).__name__}: {e}"
            logger.error(error_msg)
            return error_msg
