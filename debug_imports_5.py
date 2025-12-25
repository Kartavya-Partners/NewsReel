try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    print("VideoFileClip explicit success")
except ImportError as e:
    print(f"VideoFileClip explicit failed: {e}")

try:
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    print("AudioFileClip explicit success")
except ImportError as e:
    print(f"AudioFileClip explicit failed: {e}")

try:
    from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
    print("concatenate explicit success")
except ImportError as e:
    print(f"concatenate explicit failed: {e}")
