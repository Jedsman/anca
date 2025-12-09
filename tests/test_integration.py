"""
Integration test for Researcher → Generator workflow
Tests the full two-agent pipeline
"""
from agents import create_researcher, create_generator
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool
from crewai import Crew, Process, Task
import time

def test_integration():
    print("=" * 60)
    print("Testing Researcher → Generator Integration")
    print("=" * 60)
    
    # Initialize tools
    scraper = ScraperTool()
    writer = FileWriterTool()
    
    # Create agents
    researcher = create_researcher(tools=[scraper])
    generator = create_generator(tools=[scraper, writer])
    
    print(f"\n🤖 Agents:")
    print(f"   1. {researcher.role} ({researcher.llm.model})")
    print(f"   2. {generator.role} ({generator.llm.model})")
    
    # Create simplified tasks
    research_task = Task(
        description="Find ONE long-tail keyword about 'coffee brewing'. Just the keyword, no scraping needed.",
        expected_output="A single keyword phrase",
        agent=researcher
    )
    
    generation_task = Task(
        description=(
            "Write a SHORT 300-word article about the keyword from the researcher. "
            "Save as 'test-integration-output.md'."
        ),
        expected_output="Confirmation of file save",
        agent=generator
    )
    
    # Create crew
    crew = Crew(
        agents=[researcher, generator],
        tasks=[research_task, generation_task],
        process=Process.sequential,
        verbose=True
    )
    
    print(f"\n⏱️  Starting crew execution...")
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
    test_integration()
