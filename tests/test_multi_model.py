"""
Test multi-model agent setup
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import create_researcher, create_generator
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool

print("Testing multi-model agent setup...")
print("=" * 60)

# Initialize tools
scraper = ScraperTool()
writer = FileWriterTool()

# Create agents (each with their own model)
researcher = create_researcher(tools=[scraper])
generator = create_generator(tools=[scraper, writer])

print(f"\n✅ Researcher Agent:")
print(f"   Role: {researcher.role}")
print(f"   Model: {researcher.llm.model}")
print(f"   Temperature: {researcher.llm.temperature}")

print(f"\n✅ Generator Agent:")
print(f"   Role: {generator.role}")
print(f"   Model: {generator.llm.model}")
print(f"   Temperature: {generator.llm.temperature}")

print("\n✅ Multi-model setup complete!")
