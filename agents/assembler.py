import os
import logging
import time
from app.core.llm_wrappers import get_llm
from langchain_core.prompts import ChatPromptTemplate

from app.state import ArticleState
from app.core.config import settings
from app.core.langchain_logging_callback import LangChainLoggingHandler

logger = logging.getLogger(__name__)

ASSEMBLER_SYSTEM_PROMPT = """You are the Senior Editor (Assembler).
Your job is to take the drafted sections of an article and assemble them into a final, polished masterpiece.

## Instructions
1.  **Synthesize**: Read the provided "Draft Sections".
2.  **Introduction**: Write a compelling, hook-driven Introduction that sets the stage (do NOT use the draft's intro if it's weak).
3.  **Body**: Stitch the provided sections together. Ensure smooth transitions between paragraphs.
    *   Preserve the technical depth and facts from the drafts.
    *   Fix any repetition or disjointed flow.
4.  **Conclusion**: Write a strong Conclusion that summarizes and gives a call to action or final thought.
5.  **Formatting**: Output the Full Markdown Article.
    *   Start with a Level 1 Title (# Title).
    *   Use proper headers (##, ###).

## Input Context
Topic: {topic}
Target Audience: {audience}
"""

def assembler_node(state: ArticleState):
    """
    Assembler Node: Stitches sections, adds Intro/Outro, and saves the file.
    """
    logger.info("[ASSEMBLER] Assembling article...")

    # 1. Sort sections by order
    # state["sections_content"] is a list of dicts: {'order': int, 'content': str}
    sorted_sections = sorted(state["sections_content"], key=lambda x: x["order"])
    
    # 2. Join content
    draft_body = "\n\n".join([s["content"] for s in sorted_sections])
    
    # 3. Setup LLM
    llm = get_llm(
        provider=state.get("provider", "gemini"),
        model=state.get("model", "gemini-flash-lite-latest"),
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name="Assembler")]
    )
    
    # 4. Prompt for assembly
    prompt = ChatPromptTemplate.from_messages([
        ("system", ASSEMBLER_SYSTEM_PROMPT),
        ("human", "Here are the draft sections:\n\n{draft_body}"),
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "topic": state["topic"],
            "audience": state["blueprint"].audience,
            "draft_body": draft_body
        })
        
        final_content = response.content
        
        # 5. Save to file
        filename = f"{state['topic'].lower().replace(' ', '_')}_{int(time.time())}.md"
        filepath = settings.articles_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        logger.info(f"[ASSEMBLER] Article saved to {filepath}")
        
        return {
            "final_article": final_content
        }
        
    except Exception as e:
        logger.error(f"[ASSEMBLER] Error assembling article: {e}")
        raise e
