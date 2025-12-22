"""Quick test of news collection."""
import sys
sys.path.insert(0, '.')

from agents.news_collection_agent import NewsCollectionAgent
from agents.base_agent import AgentState
import yaml

# Load config
with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create agent
agent = NewsCollectionAgent(config)

# Test with technology topic
state = AgentState(topic='technology')
result = agent.execute(state)

# Print results
print(f"\n✓ News collection successful!")
print(f"  Articles found: {len(result.raw_articles)}")

if result.raw_articles:
    print(f"\n  Sample article:")
    print(f"    Title: {result.raw_articles[0]['title'][:70]}...")
    print(f"    Source: {result.raw_articles[0]['source']}")
else:
    print("\n  ⚠ No articles found - check internet connection or try different topic")
