
import sys
import os
from pathlib import Path

def check_imports():
    print("Checking MoviePy imports...")
    try:
        # Test the imports exactly as used in VideoComposerAgent
        from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
        # In MoviePy v2, vfx and afx might need specific paths if not exposed at top level
        try:
            from moviepy import vfx, afx
            print("  [OK] from moviepy import vfx, afx")
        except ImportError:
            print("  [FAIL] 'from moviepy import vfx, afx' failed. Trying submodule...")
            try:
                import moviepy.video.fx.all as vfx
                import moviepy.audio.fx.all as afx
                print("  [OK] Submodule import succeeded.")
            except ImportError as e:
                print(f"  [ERROR] Could not import vfx/afx: {e}")
                return False
                
        print("  [OK] Core MoviePy classes imported.")
        return True
    except ImportError as e:
        print(f"  [ERROR] MoviePy Import Failed: {e}")
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error: {e}")
        return False

def check_assets():
    print("\nChecking Assets...")
    music_path = Path(r"c:\Users\HP\Desktop\kartavya_submission\Audio asset\soft-ambient-background-music-454933.mp3")
    if music_path.exists():
        print(f"  [OK] Music file found: {music_path.name}")
        return True
    else:
        print(f"  [ERROR] Music file MISSING at: {music_path}")
        return False

if __name__ == "__main__":
    if check_imports() and check_assets():
        print("\n✅ SYSTEM VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("\n❌ SYSTEM VERIFICATION FAILED")
        sys.exit(1)
