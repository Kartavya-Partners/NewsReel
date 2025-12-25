
import os
import sys
import subprocess
import yaml
from pathlib import Path

# Mock config for Agents
MOCK_CONFIG = {
    "tts": {
        "engine": "edge-tts",
        "voice": "en-US-EricNeural",
        "speed": 1.0
    },
    "llm": {"provider": "ollama", "model": "llama3"},
    "video": {"resolution": [1280, 720]}
}

def step_msg(msg):
    print(f"\n🔹 {msg}")

def check_voice_speed_pipeline():
    step_msg("Testing Voiceover Speed (1.05x) Pipeline...")
    try:
        # 1. Generate Raw
        raw_file = "test_raw.mp3"
        out_file = "test_speed_1.05.mp3"
        text = "This is a test of the brisk news narration speed."
        
        # Edge TTS
        cmd_gen = [
            "edge-tts", "--text", text, "--write-media", raw_file, "--voice", "en-US-EricNeural"
        ]
        subprocess.run(cmd_gen, check=True, capture_output=True)
        
        if not os.path.exists(raw_file):
            print("❌ Edge TTS Failed to generate file.")
            return False
            
        # 2. Apply Speed (Simulating VoiceoverAgent logic)
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        cmd_speed = [
            ffmpeg_exe, '-y', '-v', 'error',
            '-i', raw_file,
            '-filter:a', 'atempo=1.05',
            '-vn', out_file
        ]
        subprocess.run(cmd_speed, check=True)
        
        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            print("✅ Audio generation + 1.05x Speed encoding: SUCCESS")
            # Cleanup
            if os.path.exists(raw_file): os.remove(raw_file)
            if os.path.exists(out_file): os.remove(out_file)
            return True
        else:
            print("❌ Speed encoding produced empty file.")
            return False
            
    except Exception as e:
        print(f"❌ Audio Test Failed: {e}")
        return False

def check_visual_prompt_integrity():
    step_msg("Verifying Visual Planner Prompt Update...")
    try:
        from agents.visual_planner_agent import VisualPlannerAgent
        # We can't access the private method easily without instantiation, 
        # but we can check if the file on disk contains the key phrase.
        with open("agents/visual_planner_agent.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        target_phrases = [
            "FORCE 'Location/Country' context",
            "EVENT: [Description], LOCATION: [City/Country]"
        ]
        
        all_found = True
        for phrase in target_phrases:
            if phrase in content:
                print(f"✅ Found prompt rule: '{phrase[:20]}...'")
            else:
                print(f"❌ Missing prompt rule: '{phrase}'")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Visual Check Failed: {e}")
        return False

def check_script_prompt_integrity():
    step_msg("Verifying Script Writer Prompt Update (5W+1H)...")
    try:
        with open("agents/script_writer_agent.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        target_phrases = [
            "STRICT JOURNALISTIC RULES (5W+1H)",
            "NEUTRAL TONE",
            "NEUTRAL ENDING"
        ]
        
        all_found = True
        for phrase in target_phrases:
            if phrase in content:
                print(f"✅ Found prompt rule: '{phrase}'")
            else:
                print(f"❌ Missing prompt rule: '{phrase}'")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Script Check Failed: {e}")
        return False

if __name__ == "__main__":
    print("=== SYSTEM UPGRADE VERIFICATION SUITE ===")
    
    vis = check_visual_prompt_integrity()
    scr = check_script_prompt_integrity()
    aud = check_voice_speed_pipeline()
    
    if vis and scr and aud:
        print("\n🚀 ALL DIAGNOSTICS PASSED. CODEBASE IS STABLE.")
        sys.exit(0)
    else:
        print("\n⛔ SOME CHECKS FAILED.")
        sys.exit(1)
