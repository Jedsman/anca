"""
Isolated test for Generator Agent
Tests agent behavior with pre-defined input
"""
from agents import create_generator
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool
from crewai import Task
import time

def test_generator():
    print("=" * 60)
    print("Testing Generator Agent in isolation")
    print("=" * 60)
    
    # Create agent
    scraper = ScraperTool()
    writer = FileWriterTool()
    generator = create_generator(tools=[scraper, writer])
    
    print(f"\n🤖 Agent: {generator.role}")
    print(f"🧠 Model: {generator.llm.model}")
    print(f"🌡️  Temperature: {generator.llm.temperature}")
    
    # Create a simple test task with pre-defined content
    test_task = Task(
        description=(
            "Write a very short (200 word) blog post about 'best grind size for french press coffee'. "
            "Use this information: Coarse grind is best for french press. "
            "Save it as 'test-generator-output.md'."
        ),
        expected_output="Confirmation that article was written to file",
        agent=generator
    )
    
    print(f"\n📋 Task: {test_task.description[:100]}...")
    print(f"\n⏱️  Starting execution...")
    
    start_time = time.time()
    result = generator.execute_task(
        task=test_task,
        context=None,
        tools=[scraper, writer]
    )
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Time: {elapsed:.2f}s")
    print(f"\n📄 Result:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    
    return result

if __name__ == "__main__":
    test_generator()
