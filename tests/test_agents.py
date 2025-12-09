"""
Quick test to verify agent refactoring works
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crewai import LLM
from agents import create_researcher, create_generator
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool

print("Testing agent module imports...")

# Set up LLM
llm = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434",
    temperature=0.7
)

# Initialize tools
scraper = ScraperTool()
writer = FileWriterTool()

# Create agents
researcher = create_researcher(llm=llm, tools=[scraper])
generator = create_generator(llm=llm, tools=[scraper, writer])

print(f"✅ Researcher: {researcher.role}")
print(f"✅ Generator: {generator.role}")
print("\n✅ All agents created successfully!")
