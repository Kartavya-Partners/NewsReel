try:
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    print("AudioFileClip submodule success")
except ImportError as e:
    print(f"AudioFileClip submodule failed: {e}")

try:
    from moviepy.video.compositing.concatenate import concatenate_videoclips
    print("concatenate submodule success")
except ImportError as e:
    print(f"concatenate submodule failed: {e}")
