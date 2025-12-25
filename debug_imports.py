try:
    from moviepy import VideoFileClip
    print("Top level success")
except ImportError:
    print("Top level failed")

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    print("Submodule io success")
except ImportError as e:
    print(f"Submodule io failed: {e}")

try:
    from moviepy.video.VideoClip import VideoClip
    print("VideoClip success")
except ImportError as e:
    print(f"VideoClip failed: {e}")
