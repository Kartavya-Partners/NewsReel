"""Simple test to verify the workflow works without Ollama."""

import sys
from pathlib import Path

# Test imports
print("Testing imports...")
try:
    from agents.base_agent import AgentState
    from agents.news_collection_agent import NewsCollectionAgent
    print("✓ Agent imports successful")
except Exception as e:
    print(f"✗ Agent import failed: {e}")
    sys.exit(1)

# Test configuration loading
print("\nTesting configuration...")
try:
    import yaml
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(f"✓ Configuration loaded: {len(config)} sections")
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    sys.exit(1)

# Test news collection (without LLM)
print("\nTesting news collection...")
try:
    news_agent = NewsCollectionAgent(config)
    state = AgentState(topic="technology")
    
    # This will try to fetch real RSS feeds
    result = news_agent.execute(state)
    
    if result.raw_articles:
        print(f"✓ News collection successful: {len(result.raw_articles)} articles")
        print(f"\nSample article:")
        print(f"  Title: {result.raw_articles[0]['title'][:60]}...")
        print(f"  Source: {result.raw_articles[0]['source']}")
    else:
        print("⚠ No articles found (check internet connection)")
        
except Exception as e:
    print(f"✗ News collection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ BASIC TESTS PASSED")
print("=" * 60)
print("\nNote: Full workflow requires Ollama to be running.")
print("Install Ollama from: https://ollama.ai")
print("Then run: ollama pull llama3")
