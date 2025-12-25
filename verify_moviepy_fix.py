
import sys
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, CompositeVideoClip, ColorClip

# Add the project directory to python path
sys.path.append(os.path.abspath("."))

from agents.animation_generator_agent import AnimationGeneratorAgent, AgentState

def verify_fix():
    print("Verifying MoviePy ImageMagick fix...")
    
    # Instantiate the agent
    agent = AnimationGeneratorAgent(config={})
    agent.temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Test _create_text_clip directly
    print("Testing _create_text_clip...")
    try:
        clip = agent._create_text_clip("Test Headline", 46, "white")
        print(f"Clip created successfully: {clip}")
        
        # Verify it has data
        if clip.img is not None:
             print("Clip has image data.")
        else:
             print("Clip image data is None.")
             
        bg = ColorClip(size=(1280, 720), color=(0,0,0)).with_duration(1)
        comp = CompositeVideoClip([bg, clip.with_position("center").with_duration(1)])
        print("CompositeVideoClip created successfully.")
        
        # Try to render a single frame
        print("Rendering a frame...")
        frame = comp.get_frame(0)
        print("Frame rendered successfully.")
        
        print("\nFix verification PASSED!")
        return 0
        
    except Exception as e:
        print(f"\nFix verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(verify_fix())
