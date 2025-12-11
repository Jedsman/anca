"""
Quick test to verify agent refactoring works
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import create_researcher, create_generator, create_auditor
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool

print("Testing agent module imports...")

# Base URL for Ollama
base_url = "http://localhost:11434"

# Initialize tools
scraper = ScraperTool()
writer = FileWriterTool()

# Create agents (factory functions create LLM internally)
researcher = create_researcher(tools=[scraper], base_url=base_url)
generator = create_generator(tools=[scraper, writer], base_url=base_url)
auditor = create_auditor(tools=[], base_url=base_url)

print(f"✅ Researcher: {researcher.role}")
print(f"✅ Generator: {generator.role}")
print(f"✅ Auditor: {auditor.role}")
print("\n✅ All agents created successfully!")
