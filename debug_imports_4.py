try:
    from moviepy import concatenate_videoclips, VideoFileClip
    print(f"Concatenate Module: {concatenate_videoclips.__module__}")
    print(f"VideoFileClip Module: {VideoFileClip.__module__}")
except ImportError as e:
    print(f"Import failed: {e}")
