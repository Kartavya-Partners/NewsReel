"""Test the full workflow with a common topic that should have news articles."""

import sys
import json
from pathlib import Path

print("=" * 60)
print("AI News Explainer - Full Workflow Test")
print("=" * 60)

# Test with a topic that's likely to have news
test_topics = [
    "artificial intelligence",
    "technology",
    "climate change",
]

print("\nTesting with topic: 'artificial intelligence'")
print("-" * 60)

try:
    from workflows.news_video_workflow import NewsVideoWorkflow
    
    # Initialize workflow
    workflow = NewsVideoWorkflow()
    
    # Run workflow
    print("\n🚀 Starting workflow...")
    result = workflow.run(
        topic="artificial intelligence",
        category="technology"
    )
    
    # Save results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "test_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
    print(f"\n📊 Results:")
    print(f"  Topic: {result['topic']}")
    print(f"  Summary length: {len(result['summary'].split())} words")
    print(f"  Narration length: {len(result['narration'].split())} words")
    print(f"  Scenes planned: {len(result['scene_plan'])}")
    
    print(f"\n💾 Full results saved to: {output_file}")
    
    print("\n📝 Summary Preview:")
    print("-" * 60)
    print(result['summary'][:200] + "..." if len(result['summary']) > 200 else result['summary'])
    
    print("\n🎬 Scene Plan:")
    print("-" * 60)
    for scene in result['scene_plan'][:3]:  # Show first 3 scenes
        print(f"  Scene {scene['scene_number']}: {scene.get('on_screen_text', 'N/A')[:50]}...")
    
    if len(result['scene_plan']) > 3:
        print(f"  ... and {len(result['scene_plan']) - 3} more scenes")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
