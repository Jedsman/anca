"""
Simple test script to verify Ollama connection with CrewAI
"""
from crewai import LLM

# Test the LLM connection
llm = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434",
    temperature=0.7
)

print("Testing Ollama connection...")
try:
    response = llm.call(
        messages=[{"role": "user", "content": "Say 'Hello, ANCA!' and nothing else."}]
    )
    print(f"✅ Success! Response: {response}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
