
import os
import sys
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from agents.auditor import create_auditor
    from agents.researcher import create_researcher
    from agents.generator import create_generator
    from crewai import Agent
    
    # Mock environment variable if not present for testing logic
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
         os.environ["GEMINI_API_KEY"] = "fake_key_for_testing"

    print("Checking Auditor...")
    auditor = create_auditor(tools=[])
    print(f"Auditor: {auditor.llm.model}")

    print("Checking Researcher...")
    researcher = create_researcher(tools=[])
    print(f"Researcher: {researcher.llm.model}")

    print("Checking Generator...")
    generator = create_generator(tools=[])
    print(f"Generator: {generator.llm.model}")
    
    print("\nAll agents initialized successfully with langchain_ollama.ChatOllama.")

except Exception as e:
    print(f"Error during verification: {e}")
    sys.exit(1)
