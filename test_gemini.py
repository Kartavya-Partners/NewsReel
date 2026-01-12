
import os
from dotenv import load_dotenv
load_dotenv()

# from config.settings import load_config
from utils.llm_client import LLMClient
import yaml

# Mock config loader since we just want to test LLM
config = {
    'provider': 'gemini',
    'model': 'gemini-flash-latest',
    'temperature': 0.1,
    'max_tokens': 100
}

def test_gemini():
    print("Testing Gemini Connection...")
    client = LLMClient(config)
    
    if not client.is_available():
        print("❌ Client reports NOT available (Check API Key)")
        return

    try:
        response = client.generate("Say 'Hello Gemini' if you can hear me.")
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_gemini()
