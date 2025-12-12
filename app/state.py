from typing import List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
import operator

class Section(BaseModel):
    heading: str = Field(description="The heading of the section")
    description: str = Field(description="Detailed description of what this section should cover")
    word_count: int = Field(description="Target word count for this section")
    search_queries: List[str] = Field(description="Search queries to research this specific section")

class Blueprint(BaseModel):
    title: str = Field(description="The title of the article")
    audience: str = Field(description="The target audience")
    sections: List[Section] = Field(description="List of sections to write")

class ArticleState(TypedDict):
    topic: str
    provider: str # "gemini", "groq", "ollama"
    model: str    # "gemini-2.0-flash", "llama3", etc.
    blueprint: Blueprint
    # Map-Reduce outputs. List of dicts: {'order': int, 'content': str}
    sections_content: Annotated[List[dict], operator.add] 
    final_article: str
