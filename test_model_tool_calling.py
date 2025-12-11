#!/usr/bin/env python
"""
Model Tool Calling Test
Tests different Ollama models to see which ones correctly call tools with content.
"""
import os
import sys
from pathlib import Path
from crewai import Agent, Task, Crew, LLM
from tools.file_writer_tool import FileWriterTool

# Models to test (in order of recommendation)
MODELS_TO_TEST = [
    "ollama/qwen2.5:14b",
    "ollama/mistral:7b-instruct-v0.3", 
    "ollama/llama3.1:8b",
    "ollama/qwen2.5:7b",
    "ollama/gemma2:9b-instruct",
]

def test_model(model_name: str) -> dict:
    """
    Test a single model's ability to call FileWriterTool correctly.
    
    Returns:
        dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"{'='*80}")
    
    try:
        # Create LLM
        llm = LLM(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0.3,
            supports_function_calling=True
        )
        
        # Create simple agent with FileWriterTool
        agent = Agent(
            role='Test Writer',
            goal='Write a short article and save it using FileWriterTool',
            backstory='You are a test agent that writes content and saves it to files.',
            llm=llm,
            tools=[FileWriterTool()],
            verbose=True
        )
        
        # Create simple task
        task = Task(
            description="""
            Write a SHORT article (exactly 100 words) about "The Benefits of Coffee" 
            and save it using FileWriterTool.
            
            CRITICAL: You MUST call FileWriterTool with TWO parameters:
            1. filename: "test-coffee-article.md"
            2. content: The FULL TEXT of your 100-word article
            
            Do NOT leave the content parameter empty. Put your entire article in the content parameter.
            """,
            expected_output="Article saved to: test-coffee-article.md",
            agent=agent
        )
        
        # Create and run crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        
        # Check if file was created
        test_file = Path("articles/test-coffee-article.md")
        
        if test_file.exists():
            content = test_file.read_text()
            word_count = len(content.split())
            
            # Clean up test file
            test_file.unlink()
            
            return {
                "model": model_name,
                "success": True,
                "word_count": word_count,
                "content_preview": content[:100]
            }
        else:
            return {
                "model": model_name,
                "success": False,
                "error": "File not created - tool call likely failed"
            }
            
    except Exception as e:
        return {
            "model": model_name,
            "success": False,
            "error": str(e)
        }


def main():
    """Run tests on all models and report results."""
    print("\n" + "="*80)
    print("OLLAMA MODEL TOOL CALLING TEST")
    print("Testing which models correctly call FileWriterTool with content")
    print("="*80)
    
    results = []
    
    for model in MODELS_TO_TEST:
        result = test_model(model)
        results.append(result)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    successful = []
    failed = []
    
    for result in results:
        if result["success"]:
            successful.append(result)
            print(f"\n✅ {result['model']}")
            print(f"   Word count: {result['word_count']}")
            print(f"   Preview: {result['content_preview']}...")
        else:
            failed.append(result)
            print(f"\n❌ {result['model']}")
            print(f"   Error: {result['error']}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if successful:
        print(f"\n✨ USE THESE MODELS (in order of preference):")
        for i, result in enumerate(successful, 1):
            print(f"{i}. {result['model']} ({result['word_count']} words generated)")
    else:
        print("\n⚠️  No models successfully called FileWriterTool with content!")
        print("\nPossible solutions:")
        print("1. Try enabling json_mode in Ollama")
        print("2. Switch to a commercial API (OpenAI, Anthropic)")
        print("3. Implement content extraction fallback")
    
    if failed:
        print(f"\n❌ AVOID THESE MODELS:")
        for result in failed:
            print(f"  - {result['model']}")
    
    print("\n" + "="*80)
    print(f"Tests complete: {len(successful)} passed, {len(failed)} failed")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
