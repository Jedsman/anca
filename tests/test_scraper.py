"""
Test the updated scraper tool to ensure it works with CrewAI agents
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.scraper_tool import ScraperTool

# Initialize the scraper
scraper = ScraperTool()

# Test with a simple URL (using a reliable test site)
print("Testing scraper tool...")
print("=" * 60)

# Use a simple, fast-loading page for testing
test_url = "https://example.com"

print(f"\nScraping: {test_url}")
print("-" * 60)

result = scraper._run(test_url)

print("\n📄 RESULT:")
print(result[:500] if len(result) > 500 else result)  # Show first 500 chars
print(f"\n... (Total length: {len(result)} characters)")
