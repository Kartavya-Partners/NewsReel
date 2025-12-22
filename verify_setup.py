"""Quick verification script to check setup."""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version >= (3, 10):
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (Need 3.10+)"

def check_import(module_name):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True, "Installed"
    except ImportError:
        return False, "Not installed"

def check_ollama():
    """Check if Ollama is available."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "Running"
        return False, "Not responding"
    except:
        return False, "Not available"

def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("AI News Explainer - Setup Verification")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("LangGraph", lambda: check_import("langgraph")),
        ("LangChain", lambda: check_import("langchain")),
        ("Feedparser", lambda: check_import("feedparser")),
        ("Requests", lambda: check_import("requests")),
        ("BeautifulSoup", lambda: check_import("bs4")),
        ("Pydantic", lambda: check_import("pydantic")),
        ("PyYAML", lambda: check_import("yaml")),
        ("Loguru", lambda: check_import("loguru")),
        ("Ollama Service", check_ollama),
    ]
    
    results = []
    for name, check_func in checks:
        status, message = check_func()
        results.append((name, status, message))
        
        symbol = "✓" if status else "✗"
        color = "\033[92m" if status else "\033[91m"
        reset = "\033[0m"
        
        print(f"{color}{symbol}{reset} {name:.<40} {message}")
    
    print("\n" + "=" * 60)
    
    passed = sum(1 for _, status, _ in results if status)
    total = len(results)
    
    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("\nYou're ready to run the AI News Explainer!")
        print("\nTry: python main.py --topic \"Artificial Intelligence\"")
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total} passed)")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        
        if not any(status for name, status, _ in results if name == "Ollama Service"):
            print("\nOllama is not running. Please:")
            print("  1. Install Ollama from https://ollama.ai")
            print("  2. Run: ollama pull llama3")
    
    print("=" * 60 + "\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
