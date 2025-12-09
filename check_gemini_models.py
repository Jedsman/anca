import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    print("Please set it in your .env file or directly in your environment.")
else:
    genai.configure(api_key=api_key)
    print("Attempting to list available Gemini models...")
    try:
        import pprint
        for model in genai.list_models():
            pprint.pprint(model)
    except Exception as e:
        print(f"An error occurred while listing models: {e}")
        print("Please ensure your GEMINI_API_KEY is valid and has access to the Gemini API.")

print("\n--- Diagnostic complete ---")
print("If you still encounter issues, please double-check your API key and its permissions.")
