
import os
import logging
import yaml
import argparse
from pathlib import Path
from typing import TypedDict, List, Annotated
from typing_extensions import NotRequired

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.tools import tool

from app.core.config import settings
from app.core.langchain_logging_callback import LangChainLoggingHandler

# --- Import Tools ---
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool
from tools.rag_tool import RAGTool
from tools.file_reader_tool import FileReaderTool

# --- Import Agents ---
from agents.researcher import create_researcher_node
from agents.generator import create_generator_node
from agents.auditor import create_auditor_node
from agents.reviser import create_reviser_node
from agents.critique import create_critique_node

# Setup Logger
logger = logging.getLogger(__name__)

# --- 1. Load Prompts ---
def load_prompt(filename: str) -> dict:
    """Load a YAML prompt file from the prompts directory."""
    prompts_dir = Path(__file__).parent / "prompts"
    file_path = prompts_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Load generic tasks
research_config = load_prompt("researcher_task.yaml")
writer_config = load_prompt("writer_task.yaml")
critique_config = load_prompt("critique_task.yaml")
auditor_config = load_prompt("auditor_task.yaml")
reviser_config = load_prompt("reviser_task.yaml")

# --- 2. Define State ---
class AgentState(TypedDict):
    topic: str
    messages: Annotated[List[BaseMessage], add_messages]
    # Optional tracking fields
    revision_count: int
    critique_count: int
    filename: NotRequired[str]

# --- 3. Setup Tools ---
# Initialize tools (singleton instances if appropriate)
scraper = ScraperTool()
file_writer = FileWriterTool()
rag = RAGTool()
file_reader = FileReaderTool()

# Define tool wrappers for agents (as seen in original implementations)
# These are kept here if main needs to access them, but agents instantiate their own currently.
# The refactored agents use tools defined INSIDE their factory or imported.
# We just need to make sure the AGENTS use the prompts we pass.

# Create Agents with Loaded Prompts
research_agent = create_researcher_node(system_prompt=research_config['description'])
writer_agent = create_generator_node(system_prompt=writer_config['description'])
critique_agent = create_critique_node(system_prompt=critique_config['description'])
auditor_agent = create_auditor_node(system_prompt=auditor_config['description'])
reviser_agent = create_reviser_node(system_prompt=reviser_config['description'])

# --- 4. Define Node Logic ---

def researcher_node(state: AgentState):
    logger.info("--- Researcher Agent ---")
    messages = state['messages']
    # If first run, inject prompt
    if not messages:
        prompt = research_config['description'].format(topic=state['topic'])
        messages = [HumanMessage(content=prompt)]
    
    result = research_agent.invoke({"messages": messages})
    return {"messages": result["messages"]}

def writer_node(state: AgentState):
    logger.info("--- Writer Agent ---")
    # Get context from previous agent
    last_message = state['messages'][-1].content
    
    instruction = writer_config['description'].format(topic=state['topic'])
    instruction += f"\n\nCONTEXT FROM RESEARCHER:\n{last_message}"
    
    result = writer_agent.invoke({"messages": [HumanMessage(content=instruction)]})
    
    # Extract filename if possible (basic heuristic)
    filename = None
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == 'save_article':
                    filename = tool_call.get('args', {}).get('filename')
                    break
    
    return {"messages": result["messages"], "filename": filename}

def critique_node(state: AgentState):
    logger.info("--- Critique Agent ---")
    count = state.get('critique_count', 0) + 1
    
    instruction = critique_config['description'].format(
        topic=state['topic'],
        target_length="1500+" # Generic target
    )
    if state.get('filename'):
        instruction += f"\n\nFILE TO CHECK: {state['filename']}"

    result = critique_agent.invoke({"messages": [HumanMessage(content=instruction)]})
    return {"messages": result["messages"], "critique_count": count}

def auditor_node(state: AgentState):
    logger.info("--- Auditor Agent ---")
    instruction = auditor_config['description'].format(topic=state['topic'])
    if state.get('filename'):
        instruction += f"\n\nFILE TO AUDIT: {state['filename']}"
        
    result = auditor_agent.invoke({"messages": [HumanMessage(content=instruction)]})
    return {"messages": result["messages"]}

def reviser_node(state: AgentState):
    logger.info("--- Reviser Agent ---")
    count = state.get('revision_count', 0) + 1
    
    # Get feedback from auditor
    last_feedback = state['messages'][-1].content
    
    instruction = reviser_config['description'].format(topic=state['topic'])
    instruction += f"\n\nFEEDBACK:\n{last_feedback}"
    
    result = reviser_agent.invoke({"messages": [HumanMessage(content=instruction)]})
    return {"messages": result["messages"], "revision_count": count}

# --- 5. Routing Logic ---

def should_loop_critique(state: AgentState) -> str:
    """Check if critique passed or failed."""
    # Simple check: max 3 attempts
    if state.get('critique_count', 0) >= 3:
        return "auditor"
    
    # Parse last message for Status
    messages = state.get('messages', [])
    if messages:
        last_msg = messages[-1].content
        if "Status: PASS" in last_msg:
            return "auditor"
            
    return "writer" # Go back to write/expand if failed

def should_loop_revision(state: AgentState) -> str:
    """Check if revision loop should continue."""
    if state.get('revision_count', 0) >= 2:
        return END
    return "auditor" # Re-audit

# --- 6. Build Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node) # previously generator
workflow.add_node("critique", critique_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("reviser", reviser_node)

# Edges
workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "critique")

workflow.add_conditional_edges(
    "critique",
    should_loop_critique,
    {
        "auditor": "auditor",
        "writer": "writer"
    }
)

workflow.add_edge("auditor", "reviser")
workflow.add_conditional_edges(
    "reviser",
    should_loop_revision,
    {
        "auditor": "auditor",
        "end": END
    }
)

app = workflow.compile()

# --- 7. Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="Artificial Intelligence", help="Topic to research and write about")
    args = parser.parse_args()
    
    print(f"Starting Agentic Workflow for: {args.topic}")
    result = app.invoke({
        "topic": args.topic,
        "messages": [],
        "revision_count": 0,
        "critique_count": 0
    })
    
    print("Workflow Completed.")
