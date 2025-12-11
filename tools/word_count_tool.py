"""
Word Count Tool for ANCA
Provides accurate word counting for Markdown content.
"""
from langchain_core.tools import tool
import markdown
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def count_markdown_words(text: str) -> int:
    """
    Calculate accurate word count from Markdown content.
    
    Converts Markdown to HTML, strips tags, and counts words.
    This provides an accurate count excluding formatting syntax.
    
    Args:
        text: Markdown content string
        
    Returns:
        Integer word count
    """
    if not text:
        return 0
    
    try:
        # Convert Markdown to HTML
        html = markdown.markdown(text)
        # Parse HTML and extract text
        soup = BeautifulSoup(html, "html.parser")
        plain_text = soup.get_text()
        # Count words
        words = plain_text.split()
        return len(words)
    except Exception as e:
        logger.warning(f"Error counting words: {e}")
        # Fallback to simple split
        return len(text.split())


@tool
def calculate_word_count(markdown_content: str) -> str:
    """
    Calculate accurate word count from Markdown content.
    
    Use this tool to get the true word count of an article,
    excluding Markdown formatting syntax.
    
    Args:
        markdown_content: The full Markdown text of the article
        
    Returns:
        A message with the word count
    """
    count = count_markdown_words(markdown_content)
    logger.info(f"Calculated word count: {count} words")
    return f"Word count: {count} words"
