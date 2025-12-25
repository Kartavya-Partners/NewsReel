
import subprocess
import sys
import os
from pathlib import Path
from moviepy import AudioFileClip, afx, CompositeAudioClip

def test_edge_tts():
    print("[1/3] Testing Edge TTS Engine...")
    test_text = "System check initiated."
    output_file = "test_voice.mp3"
    
    try:
        cmd = [
            "edge-tts",
            "--text", test_text,
            "--write-media", output_file,
            "--voice", "en-US-EricNeural"
        ]
        # Run CLI
        subprocess.run(cmd, check=True, capture_output=True)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
            print("   ✅ Edge TTS generated audio successfully.")
            os.remove(output_file)
            return True
        else:
            print("   ❌ Edge TTS produced empty file.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Edge TTS Failed. Error: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        print("   ❌ 'edge-tts' binary not found. Is it installed?")
        return False

def test_moviepy_music():
    print("\n[2/3] Testing Music & AudioLoop...")
    music_path = Path(r"c:\Users\HP\Desktop\kartavya_submission\Audio asset\soft-ambient-background-music-454933.mp3")
    
    if not music_path.exists():
        print(f"   ❌ Music file missing at {music_path}")
        return False
        
    try:
        # Load clip
        clip = AudioFileClip(str(music_path))
        # Test Loop syntax (v2)
        looped = clip.with_effects([afx.AudioLoop(duration=5.0)])
        duration = looped.duration
        
        if abs(duration - 5.0) < 0.1:
            print("   ✅ MoviePy AudioLoop syntax is correct.")
            clip.close()
            return True
        else:
             print(f"   ❌ loop duration mismatch: {duration}")
             return False
    except AttributeError:
        print("   ❌ AttributeError: afx.AudioLoop not found (Version mismatch).")
        return False
    except Exception as e:
         print(f"   ❌ MoviePy Error: {e}")
         return False

def check_settings():
    print("\n[3/3] Checking Integration Settings...")
    # Just a sanity check that settings.yaml exists and has keywords
    try:
        with open("config/settings.yaml", "r") as f:
            content = f.read()
            if "edge-tts" in content and "en-US-EricNeural" in content:
                print("   ✅ Settings configured for Eric/EdgeTTS.")
                return True
            else:
                print("   ⚠️ Settings might not be saved? 'edge-tts' not found in yaml.")
                # Non-fatal but worth noting
                return True
    except:
        return False

if __name__ == "__main__":
    print("=== FINAL SYSTEM VERIFICATION ===\n")
    
    p1 = test_edge_tts()
    p2 = test_moviepy_music()
    p3 = check_settings()
    
    if p1 and p2 and p3:
        print("\n🚀 ALL SYSTEMS SPREAD. READY FOR GENERATION.")
        sys.exit(0)
    else:
        print("\n⛔ SYSTEM CHECKS FAILED. See above.")
        sys.exit(1)
