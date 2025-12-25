from moviepy import ColorClip
# from moviepy.audio.io.AudioFileClip import AudioFileClip 
# AudioArrayClip is safer for generation
from moviepy import AudioArrayClip
import numpy as np

def test_video_write():
    print("Testing write_videofile...")
    clip = ColorClip(size=(100,100), color=(0,0,0), duration=1)
    try:
        clip.write_videofile("test.mp4", fps=24, logger=None)
        print("Video write success")
    except TypeError as e:
        print(f"Video write failed: {e}")
    except Exception as e:
        print(f"Video write error: {e}")

def test_audio_write():
    print("Testing write_audiofile...")
    # Create silent audio
    silence = np.zeros((44100, 2))
    audio = AudioArrayClip(silence, fps=44100)
    try:
        audio.write_audiofile("test.mp3", fps=44100, logger=None)
        print("Audio write success")
    except TypeError as e:
        print(f"Audio write failed: {e}")
    except Exception as e:
        print(f"Audio write error: {e}")

if __name__ == "__main__":
    test_video_write()
    test_audio_write()
