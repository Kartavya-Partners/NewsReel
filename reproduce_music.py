
import os
from pathlib import Path
from moviepy import AudioFileClip, afx, CompositeAudioClip

# Mock Final Video Duration
VIDEO_DURATION = 10.0

def reproduce_music_mix():
    print("=== Reproducing Music Mix Error ===")
    music_path = Path(r"c:\Users\HP\Desktop\kartavya_submission\Audio asset\soft-ambient-background-music-454933.mp3")
    
    if not music_path.exists():
        print(f"ERROR: Music file not found at {music_path}")
        return

    try:
        print(f"Loading music: {music_path.name}")
        bg_music = AudioFileClip(str(music_path))
        
        print(f"Attempting afx.AudioLoop(duration={VIDEO_DURATION})...")
        # THIS IS THE FIX
        loop_music = bg_music.with_effects([afx.AudioLoop(duration=VIDEO_DURATION)])
        
        print("SUCCESS: audio_loop passed.")
        
        print("Attempting volume/fade...")
        loop_music = loop_music.with_volume_scaled(0.12)
        loop_music = loop_music.with_effects([afx.AudioFadeIn(1.0), afx.AudioFadeOut(2.0)])
        
        print("SUCCESS: Full Music Mix logic passed.")
        
    except AttributeError as e:
        print(f"\nCRASH DETECTED: {e}")
        # Introspect afx to see what IS available
        print(f"\nAvailable attributes in afx: {dir(afx)}")
    except Exception as e:
        print(f"\nGeneric Error: {e}")

if __name__ == "__main__":
    reproduce_music_mix()
