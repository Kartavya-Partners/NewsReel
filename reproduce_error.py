
import sys
import os
from pathlib import Path
from agents.animation_generator_agent import AnimationGeneratorAgent

# Mock Config
config = {
    "llm": {"model": "test"}, 
    "video": {"text_color": "#ffffff"},
    "animation": {"fps": 24, "resolution": "1080p"},
    "paths": {"temp_dir": "temp_verify", "output_dir": "output_verify"}
}

def reproduce():
    print("=== Reproducing Broadcasting Error ===")
    
    # Setup
    Path("temp_verify").mkdir(exist_ok=True)
    agent = AnimationGeneratorAgent(config)
    
    # Mock Data
    scene = {
        "duration": 5,
        "visual_assets": {"image_path": "assets/placeholders/news_generic.jpg"},
        "visual": {
            "lower_third_text": "TEST HEADLINE THAT IS LONG ENOUGH",
            "camera_motion": "zoom_in"
        },
        "location": "DELHI"
    }
    
    # Ensure dummy image exists
    img_path = Path("assets/placeholders/news_generic.jpg")
    if not img_path.exists():
        img_path.parent.mkdir(parents=True, exist_ok=True)
        from PIL import Image
        Image.new('RGB', (1280, 720), 'blue').save(img_path)

    try:
        print("Attempting to render scene...")
        # This calls _render_scene -> _create_lower_third -> CompositeVideoClip
        agent._render_scene(scene, 999, "Test Topic")
        print("SUCCESS: Scene rendered without crash.")
    except Exception as e:
        print(f"\nCRASH DETECTED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
