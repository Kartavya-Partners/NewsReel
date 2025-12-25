
from moviepy import VideoFileClip
import os

video_path = r"c:\Users\HP\Desktop\kartavya_submission\output\Delhi_Air_Pollution_20251225_010809.mp4"

if not os.path.exists(video_path):
    print(f"Error: File not found at {video_path}")
else:
    try:
        clip = VideoFileClip(video_path)
        print(f"--- Video Inspection ---")
        print(f"Filename: {os.path.basename(video_path)}")
        print(f"Duration: {clip.duration} seconds")
        print(f"Resolution: {clip.size} (Width x Height)")
        print(f"FPS: {clip.fps}")
        print(f"Audio: {'Yes' if clip.audio else 'No'}")
        clip.close()
    except Exception as e:
        print(f"Error reading video: {e}")
