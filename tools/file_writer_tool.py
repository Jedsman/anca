import os
import logging
from pathlib import Path
from datetime import datetime
from crewai.tools import BaseTool

# Configure logging
logger = logging.getLogger(__name__)


from typing import Type
from pydantic import BaseModel, Field

class FileWriterToolSchema(BaseModel):
    """Input for FileWriterTool."""
    filename: str = Field(..., description="The filename (e.g., 'topic-guide.md'). Do NOT include 'articles/' prefix.")
    content: str = Field(..., description="The complete text content to write to the file.")

class FileWriterTool(BaseTool):
    name: str = "FileWriterTool"
    description: str = (
        "Writes content to a file in the 'articles' directory. "
        "Provide the content and filename (e.g., 'my-article.md'). "
        "The tool will automatically create backups and validate content before saving."
    )
    args_schema: Type[BaseModel] = FileWriterToolSchema

    def _run(self, filename: str, content: str) -> str:
        """
        Write content to a file in the articles directory with versioning and validation.
        
        Args:
            filename: The name of the file (e.g., 'my-article.md')
            content: The content to write to the file
            
        Returns:
            Success or error message
        """
        # TODO: Re-enable after fixing logger
        # from app.core.tool_call_logger import log_tool_call
        # log_tool_call(
        #     tool_name="FileWriterTool",
        #     arguments={
        #         "filename": filename,
        #         "content_length": len(content),
        #         "content_preview": content[:100] if content else "[EMPTY]",
        #         "word_count": len(content.split()) if content else 0
        #     }
        # )
        
        try:
            # Get the absolute path to the articles directory
            base_dir = Path(__file__).parent.parent
            articles_dir = base_dir / 'articles'
            versions_dir = articles_dir / '.versions'
            
            # Create directories if they don't exist
            articles_dir.mkdir(parents=True, exist_ok=True)
            versions_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directories exist: {articles_dir}")
            
            # Normalize filename
            clean_filename = Path(filename).name  # Remove any directory components
            if not clean_filename.lower().endswith('.md'):
                clean_filename += '.md'
                logger.info(f"Added .md extension to filename: {clean_filename}")
            
            file_path = articles_dir / clean_filename
            
            # FALLBACK: If content is empty, try to extract from context
            if not content or len(content.strip()) < 50:
                logger.warning(f"Content is empty or too short ({len(content)} chars). Attempting extraction from context...")
                
                # Try to get content from the agent's response in the conversation context
                # This is a workaround for CrewAI's ReAct mode not passing content properly
                try:
                    from app.core.content_extraction import extract_markdown_from_text, clean_extracted_content
                    
                    # Get the current conversation context from CrewAI (if available)
                    # This is hacky but necessary given CrewAI's limitations
                    import inspect
                    frame = inspect.currentframe()
                    # Walk up the stack to find agent's last response
                    for _ in range(10):
                        if frame is None:
                            break
                        frame = frame.f_back
                        if frame and 'result' in frame.f_locals:
                            result_obj = frame.f_locals['result']
                            if hasattr(result_obj, 'raw'):
                                potential_content = str(result_obj.raw)
                                extracted = extract_markdown_from_text(potential_content)
                                if extracted:
                                    extracted = clean_extracted_content(extracted)
                                    if len(extracted) > 200:
                                        logger.info(f"✅ Extracted {len(extracted)} chars from agent context!")
                                        content = extracted
                                        break
                except Exception as e:
                    logger.error(f"Content extraction failed: {e}")
            
            # CRITICAL VALIDATION: Check content is substantial
            content_stripped = content.strip()
            word_count = len(content_stripped.split())
            
            if len(content_stripped) < 100:
                error_msg = (
                    f"❌ ERROR: Content is EMPTY or too short ({len(content_stripped)} chars).\n\n"
                    f"YOU MUST PASS THE FULL ARTICLE TEXT IN THE 'content' PARAMETER.\n\n"
                    f"WRONG: FileWriterTool(filename='x.md', content='')\n"
                    f"RIGHT: FileWriterTool(filename='x.md', content='# Title\\n\\nFull article text here...')\n\n"
                    f"Do NOT just write the article in your response - PUT IT IN THE content PARAMETER."
                )
                logger.error(error_msg)
                return error_msg
            
            if word_count < 50:
                error_msg = f"❌ REJECTED: Content too short ({word_count} words). Minimum 50 words required."
                logger.error(error_msg)
                return error_msg
            
            # BACKUP: If file exists, create backup before overwriting
            if file_path.exists():
                try:
                    existing_content = file_path.read_text(encoding='utf-8')
                    existing_word_count = len(existing_content.split())
                    
                    # Create timestamped backup
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_name = f"{file_path.stem}_v{timestamp}.md"
                    backup_path = versions_dir / backup_name
                    
                    backup_path.write_text(existing_content, encoding='utf-8')
                    logger.info(f"📦 Backed up existing file ({existing_word_count} words) to: {backup_path.name}")
                    
                    # SAFETY CHECK: Warn if new content is much shorter than existing
                    if word_count < existing_word_count * 0.5:
                        warning_msg = (
                            f"⚠️ WARNING: New content ({word_count} words) is significantly shorter "
                            f"than existing ({existing_word_count} words). "
                            f"Backup saved to .versions/{backup_name}"
                        )
                        logger.warning(warning_msg)
                        # Still save, but warn
                    
                except Exception as backup_error:
                    logger.error(f"Failed to create backup: {backup_error}")
                    # Continue anyway - better to save than to fail
            
            # Write the new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ Successfully wrote {len(content)} chars (~{word_count} words) to {file_path}")
            
            return (
                f"✅ Successfully wrote article to: {clean_filename}\n"
                f"Content: {word_count} words, {len(content)} characters"
            )
            
        except Exception as e:
            error_msg = f"❌ Error writing to file '{filename}': {type(e).__name__}: {e}"
            logger.error(error_msg)
            return error_msg
