"""Quick test with optimized settings."""

print("Testing optimized workflow...")
print("=" * 60)

# Test with simple topic
import sys
from workflows.news_video_workflow import NewsVideoWorkflow

try:
    workflow = NewsVideoWorkflow()
    
    print("\n🚀 Running workflow with topic: 'technology'")
    print("   (Using optimized prompts and retry logic)")
    print("-" * 60)
    
    result = workflow.run(
        topic="technology",
        category="technology"
    )
    
    print("\n✅ SUCCESS!")
    print("=" * 60)
    print(f"Summary: {result['summary'][:150]}...")
    print(f"\nNarration: {result['narration'][:150]}...")
    print(f"\nScenes: {len(result['scene_plan'])}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
