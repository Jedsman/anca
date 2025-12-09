"""
Isolated test for Researcher Agent
Tests agent behavior with a simple task
"""
from agents import create_researcher
from tools.scraper_tool import ScraperTool
from crewai import Task
import time

def test_researcher():
    print("=" * 60)
    print("Testing Researcher Agent in isolation")
    print("=" * 60)
    
    # Create agent
    scraper = ScraperTool()
    researcher = create_researcher(tools=[scraper])
    
    print(f"\n🤖 Agent: {researcher.role}")
    print(f"🧠 Model: {researcher.llm.model}")
    print(f"🌡️  Temperature: {researcher.llm.temperature}")
    
    # Create a simple test task
    test_task = Task(
        description=(
            "Find a specific long-tail keyword related to 'home coffee brewing'. "
            "Just provide the keyword, no need to scrape websites. "
            "Keep it simple and fast."
        ),
        expected_output="A single long-tail keyword phrase",
        agent=researcher
    )
    
    print(f"\n📋 Task: {test_task.description[:100]}...")
    print(f"\n⏱️  Starting execution...")
    
    start_time = time.time()
    result = researcher.execute_task(
        task=test_task,
        context=None,
        tools=[scraper]
    )
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Time: {elapsed:.2f}s")
    print(f"\n📄 Result:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    
    return result

if __name__ == "__main__":
    test_researcher()
