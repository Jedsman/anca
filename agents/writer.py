import os
import logging
from app.core.llm_wrappers import get_llm
from langchain_core.prompts import ChatPromptTemplate

from app.state import Section
from app.core.langchain_logging_callback import LangChainLoggingHandler
from tools.rag_tool import RAGTool

logger = logging.getLogger(__name__)

# Initialize RAG tool (shared instance or new per node? New is safer for threads)
# We'll instantiate inside the node or use a global if thread-safe.
# RAGTool uses ChromaDB PersistentClient which is thread-safe.

# --- System Prompt ---
WRITER_SYSTEM_PROMPT = """You are a specialist writer for a high-end publication. 
You are responsible for writing ONE specific section of a larger article.

## Your Task
Write the section: "{heading}"

## Instructions
*   **Context**: Use the provided research context below.
*   **Goal**: Write a comprehensive, dense, and engaging section.
*   **Length**: Aim for ~{word_count} words.
*   **Style**: Professional, authoritative, yet accessible. match the tone of a premium blog post.
*   **Formatting**: Use Markdown. You may use subheaders (###) if needed, but do NOT include the main section header (it will be added by the assembler).

## Context from Research
{context}

## Description of what to cover
{description}
"""

def writer_node(state: dict):
    """
    Writer Node: Receives a dict {"section": Section, "order": int}, perfroms research, and writes.
    """
    section = state["section"]
    order = state["order"]
    
    logger.info(f"[WRITER] Processing section {order}: {section.heading}")
    
    # 1. Setup LLM
    # Expect provider/model to be passed in state dict from the Map step
    provider = state.get("provider", "gemini")
    model = state.get("model", "gemini-flash-lite-latest")

    llm = get_llm(
        provider=provider,
        model=model,
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name=f"Writer-{section.heading[:10]}")]
    )

    # 2. Perform Research (Deterministic)
    rag = RAGTool()
    context_parts = []
    
    # Execute the queries planned by the Editor-in-Chief
    for query in section.search_queries:
        logger.info(f"[WRITER] Searching: {query}")
        result = rag._run(action="retrieve", query=query)
        context_parts.append(f"--- Query: {query} ---\n{result}\n")
    
    full_context = "\n".join(context_parts)
    
    # 3. Create Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_SYSTEM_PROMPT),
        ("human", "Write the section now."),
    ])
    
    # 4. Generate
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "heading": section.heading,
            "word_count": section.word_count,
            "context": full_context,
            "description": section.description
        })
        
        content = response.content
        logger.info(f"[WRITER] Section '{section.heading}' written ({len(content)} chars).")
        
        formatted_section = f"## {section.heading}\n\n{content}\n\n"
        
        # Return structured output for the map-reduce accumulator
        # We must return a dict with the key matching the state field we want to update.
        return {"sections_content": [{"order": order, "content": formatted_section}]}
        
    except Exception as e:
        logger.error(f"[WRITER] Error writing section {state.heading}: {e}")
        # Return "error" placeholder or raise?
        # Better to return a placeholder so the whole article doesn't fail, 
        # but ideally we retry. For now, fail loud or return empty.
        return [f"## {state.heading}\n\n(Error writing this section: {e})\n\n"]
