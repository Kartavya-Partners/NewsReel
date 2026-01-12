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
        
        from moviepy import CompositeAudioClip, AudioFileClip, vfx, afx
        
        clips_with_audio = []

        # 1. Sync Logic (Match Video to Audio Duration)
        for i, (clip_path, audio_path) in enumerate(zip(scene_clips, audio_files)):
            self.log_progress(f"Processing scene {i + 1}/{len(scene_clips)}")

            try:
                video_clip = VideoFileClip(clip_path)
                audio_clip = AudioFileClip(audio_path)

                video_dur = video_clip.duration
                audio_dur = audio_clip.duration
                
                # Check for Narration Cut-off
                if audio_dur > video_dur:
                    # Case A: Audio is longer -> Extend Video (Freeze Frame)
                    diff = audio_dur - video_dur
                    self.log_progress(f"Scene {i+1}: Audio ({audio_dur}s) > Video ({video_dur}s). Extending video by {diff:.2f}s")
                    
                    # Create a freeze frame of the last frame
                    # We can simply use .with_duration on the video_clip if it's an ImageClip, 
                    # but here it's likely a CompositeVideoClip (Animation).
                    # Best way: vfx.freeze? Or just append a static ImageClip of the last frame.
                    # Simpler: MoviePy's loop/freeze might be complex.
                    # Best Safe Method: Append a frozen frame clip.
                    last_frame_clip = video_clip.to_ImageClip(t=video_dur - 0.01).with_duration(diff + 0.1)
                    
                    # Combine original + freeze
                    video_clip = concatenate_videoclips([video_clip, last_frame_clip])
                    
                    # Now match exactly to audio
                    video_clip = video_clip.with_duration(audio_dur)
                    
                else:
                    # Case B: Video is longer -> Trim Video slightly (or keep, but audio ends early)
                    # User prefers FULL narration. So we just ensure video covers it.
                    # We match video to audio duration exactly to keep pacing tight?
                    # Or let video finish? "Narrated to the whole scene"
                    # Ideally: Match max(video, audio).
                    # If video is 5s longer, it's boring silence.
                    # Let's Trim video to audio + 0.5s buffer.
                    final_dur = audio_dur + 0.1
                    video_clip = video_clip.with_duration(final_dur)

                video_with_audio = video_clip.with_audio(audio_clip)
                clips_with_audio.append(video_with_audio)

            except Exception as e:
                self.log_progress(f"Error processing scene {i}: {e}", level="error")
                continue

        if not clips_with_audio:
            raise ValueError("No valid clips to compose")

        self.log_progress("Concatenating scenes with Transitions (Dissolve)")
        
        # Apply Crossfade Transition (0.75s overlap)
        # We fade in each clip (except first) to create a smooth dissolve
        for i in range(1, len(clips_with_audio)):
            clips_with_audio[i] = clips_with_audio[i].with_effects([vfx.CrossFadeIn(0.75)])
            
        final_video = concatenate_videoclips(clips_with_audio, method="compose", padding=-0.75)
        
        # 2. Add Background Music (User Request)
        music_path = Path(r"c:\Users\HP\Desktop\kartavya_submission\Audio asset\soft-ambient-background-music-454933.mp3")
        
        if music_path.exists():
            self.log_progress("Adding Background Music...")
            try:
                bg_music = AudioFileClip(str(music_path))
                
                # Loop to match video duration
                # FIX: Use AudioLoop Effect Class for MoviePy v2
                bg_music = bg_music.with_effects([afx.AudioLoop(duration=final_video.duration)])
                
                # Volume (Low - 0.12)
                bg_music = bg_music.with_volume_scaled(0.12)
                
                # Fades
                # fadein(1.0)
                bg_music = bg_music.with_effects([afx.AudioFadeIn(1.0), afx.AudioFadeOut(2.0)])
                
                # Composite Audio (Narration + Music)
                # Ensure narration is loud enough
                original_audio = final_video.audio
                final_audio = CompositeAudioClip([original_audio, bg_music])
                
                final_video = final_video.with_audio(final_audio)
                
            except Exception as e:
                self.log_progress(f"Music Mix Failed: {e}", level="warning")
        else:
             self.log_progress(f"Background music file not found at {music_path}", level="warning")

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
        # Suppress WinError 6 (Invalid Handle) which occurs if ffmpeg process is already closed
        try:
             final_video.close()
        except Exception:
             pass
             
        for clip in clips_with_audio:
            try:
                clip.close()
            except Exception:
                pass
                
        # Explicitly close music if it exists to be safe
        try:
            if 'bg_music' in locals():
                bg_music.close()
        except Exception:
            pass

        return output_path
