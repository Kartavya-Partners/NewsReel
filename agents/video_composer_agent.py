"""
Video Composer Agent
Combines scene videos and voiceovers into the final MP4.
"""

from typing import List
from pathlib import Path
from datetime import datetime

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips

from .video_generator_agent import VideoGeneratorAgent
from .base_agent import AgentState


class VideoComposerAgent(VideoGeneratorAgent):
    """Agent responsible for composing the final video."""

    def execute(self, state: AgentState) -> AgentState:
        if not self.validate_input(state, ["scene_clips", "audio_files"]):
            return state

        self.log_progress("Composing final video")

        video_path = self._compose_video(
            state.scene_clips,
            state.audio_files,
            state.topic
        )

        state.video_path = str(video_path)
        self.log_progress(f"Video saved to: {video_path}")

        return state

    def _compose_video(
        self,
        scene_clips: List[str],
        audio_files: List[str],
        topic: str
    ) -> Path:

        clips_with_audio = []

        for i, (clip_path, audio_path) in enumerate(zip(scene_clips, audio_files)):
            self.log_progress(f"Processing scene {i + 1}/{len(scene_clips)}")

            try:
                video_clip = VideoFileClip(clip_path)
                audio_clip = AudioFileClip(audio_path)

                video_duration = video_clip.duration
                audio_duration = audio_clip.duration

                # ---- SAFE duration sync (critical fix) ----
                final_duration = min(video_duration, audio_duration) - 0.05

                if final_duration <= 0:
                    self.log_progress(
                        f"Invalid duration for scene {i}, skipping",
                        level="warning"
                    )
                    video_clip.close()
                    audio_clip.close()
                    continue

                video_clip = video_clip.with_duration(final_duration)
                audio_clip = audio_clip.with_duration(final_duration)

                video_with_audio = video_clip.with_audio(audio_clip)
                clips_with_audio.append(video_with_audio)

            except Exception as e:
                self.log_progress(f"Error processing scene {i}: {e}", level="error")
                continue

        if not clips_with_audio:
            raise ValueError("No valid clips to compose")

        self.log_progress("Concatenating scenes")
        final_video = concatenate_videoclips(clips_with_audio, method="compose")

        # ---- Output filename ----
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(
            c for c in topic if c.isalnum() or c in (" ", "-", "_")
        ).strip().replace(" ", "_")[:50]

        output_path = self.output_dir / f"{safe_topic}_{timestamp}.mp4"

        self.log_progress(f"Writing final video: {output_path.name}")
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec=self.video_config.get("codec", "libx264"),
            audio_codec=self.video_config.get("audio_codec", "aac"),
            bitrate=self.video_config.get("bitrate", "5000k"),
            logger=None
        )

        # ---- Cleanup ----
        for clip in clips_with_audio:
            clip.close()
        final_video.close()

        return output_path
