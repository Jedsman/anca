"""
Test Stage 3 Integration
Tests full workflow with RAG and SEO Auditor
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import create_researcher, create_generator, create_auditor
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool
from tools.rag_tool import RAGTool
from crewai import Crew, Process, Task
import time

def test_stage3():
    print("=" * 60)
    print("Testing Stage 3: RAG + SEO Auditor Integration")
    print("=" * 60)
    
    # Initialize tools
    scraper = ScraperTool()
    writer = FileWriterTool()
    rag = RAGTool()
    
    # Create agents
    researcher = create_researcher(tools=[scraper])
    generator = create_generator(tools=[scraper, writer, rag])
    auditor = create_auditor(tools=[])
    
    print(f"\n🤖 Agents:")
    print(f"   1. {researcher.role} ({researcher.llm.model})")
    print(f"   2. {generator.role} ({generator.llm.model})")
    print(f"   3. {auditor.role} ({auditor.llm.model})")
    
    # Simplified tasks for testing
    research_task = Task(
        description="Find ONE long-tail keyword about 'pour over coffee'. Just the keyword.",
        expected_output="A single keyword phrase",
        agent=researcher
    )
    
    generation_task = Task(
        description=(
            "Write a SHORT 200-word article about the keyword. "
            "Save as 'test-stage3-output.md'."
        ),
        expected_output="Confirmation of file save",
        agent=generator,
        context=[research_task]
    )
    
    audit_task = Task(
        description=(
            "Review the article. Provide:\n"
            "1. Quality score (1-10)\n"
            "2. One strength\n"
            "3. One improvement\n"
            "Keep it brief."
        ),
        expected_output="Quality report",
        agent=auditor,
        context=[generation_task]
    )
    
    # Create crew
    crew = Crew(
        agents=[researcher, generator, auditor],
        tasks=[research_task, generation_task, audit_task],
        process=Process.sequential,
        verbose=True
    )
    
    print(f"\n⏱️  Starting Stage 3 workflow...")
    start_time = time.time()
    
    result = crew.kickoff()
    
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    print(f"\n📄 Final result:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    
    return result

if __name__ == "__main__":
    test_stage3()
