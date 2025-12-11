"""
Content extraction fallback for when agents fail to pass content to FileWriterTool.

This extracts markdown content from the agent's response text when they call
FileWriterTool with empty content.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_markdown_from_text(text: str) -> Optional[str]:
    """
    Extract markdown content from agent's response text.
    
    Looks for patterns like:
    - Markdown headers (# Title)
    - Multiple paragraphs
    - Lists, etc.
    
    Returns the largest contiguous block of markdown-like text.
    """
    if not text:
        return None
    
    # Strategy 1: Look for markdown between triple backticks
    markdown_blocks = re.findall(r'```markdown\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if markdown_blocks:
        # Return the longest block
        longest = max(markdown_blocks, key=len)
        if len(longest.strip()) > 200:
            logger.info(f"Extracted markdown from ``` block ({len(longest)} chars)")
            return longest.strip()
    
    # Strategy 2: Look for content between any triple backticks
    any_code_blocks = re.findall(r'```\s*(.*?)\s*```', text, re.DOTALL)
    for block in any_code_blocks:
        # Check if it looks like markdown (has # headers)
        if '#' in block and len(block.strip()) > 200:
            logger.info(f"Extracted markdown-like content from code block ({len(block)} chars)")
            return block.strip()
    
    # Strategy 3: Extract everything after "Final Answer:" or similar
    final_answer_patterns = [
        r'Final Answer:\s*(.*)',
        r'Here is the article:\s*(.*)',
        r'Article content:\s*(.*)',
    ]
    
    for pattern in final_answer_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            # Check if it starts with markdown header
            if content.startswith('#') and len(content) > 200:
                logger.info(f"Extracted content after '{pattern}' ({len(content)} chars)")
                return content
    
    # Strategy 4: Look for large block starting with # header
    # Find all lines, identify markdown sections
    lines = text.split('\n')
    markdown_start = None
    markdown_lines = []
    
    for i, line in enumerate(lines):
        # Look for h1 header as start
        if line.strip().startswith('# ') and not markdown_start:
            markdown_start = i
            markdown_lines = [line]
        elif markdown_start is not None:
            # Continue collecting lines
            markdown_lines.append(line)
            
            # Stop if we hit obvious non-markdown
            if line.strip().startswith('Thought:') or line.strip().startswith('Action:'):
                markdown_lines = markdown_lines[:-1]  # Remove the last line
                break
    
    if markdown_lines:
        content = '\n'.join(markdown_lines).strip()
        if len(content) > 200:
            logger.info(f"Extracted markdown starting from H1 header ({len(content)} chars)")
            return content
    
    # Nothing found
    logger.warning("Could not extract markdown content from agent response")
    return None


def clean_extracted_content(content: str) -> str:
    """
    Clean up extracted content to remove artifacts.
    """
    if not content:
        return content
    
    # Remove common artifacts
    content = re.sub(r'\[insert.*?\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[placeholder.*?\]', '', content, flags=re.IGNORECASE)
    
    # Remove trailing "Thought:" or "Action:" if present
    content = re.sub(r'\n\s*(Thought|Action):.*$', '', content, flags=re.DOTALL)
    
    return content.strip()
