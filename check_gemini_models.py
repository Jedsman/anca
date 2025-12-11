import os
import sys

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please ensure google-generativeai and python-dotenv are installed.")
    sys.exit(1)

def list_models():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not set in environment.")
        return

    print(f"Using API Key: {api_key[:8]}...****")
    
    try:
        genai.configure(api_key=api_key)
        print("\nFetching available models compatible with generateContent...")
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name} (Display Name: {m.display_name})")
                found = True
        
        if not found:
            print("No models found that support generateContent.")

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Checking Gemini Models...")
    list_models()
