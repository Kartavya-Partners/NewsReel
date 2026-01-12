"""Voiceover Agent - Generates audio narration for scenes."""

from typing import Dict, Any, List
from pathlib import Path
from .video_generator_agent import VideoGeneratorAgent
from .base_agent import AgentState
from gtts import gTTS
import hashlib


class VoiceoverAgent(VideoGeneratorAgent):
    """Agent responsible for generating voiceover audio."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tts_config = config.get('tts', {})
        self.engine = self.tts_config.get('engine', 'gtts')
        self.voice = self.tts_config.get('voice', 'en')
        self.speed = self.tts_config.get('speed', 1.0)
        
        # Cache directory for audio files
        self.audio_cache_dir = self.temp_dir / 'audio_cache'
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Generate voiceover audio for each scene.
        
        Args:
            state: Current agent state with scene_plan
            
        Returns:
            Updated state with audio_files (list of file paths)
        """
        if not self.validate_input(state, ['scene_plan']):
            return state
        
        # Determine isolation directory
        run_id = getattr(state, 'run_id', 'default')
        run_audio_dir = self.audio_cache_dir / run_id
        run_audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_progress(f"Generating voiceover audio (Run ID: {run_id})")
        
        audio_files = []
        
        for i, scene in enumerate(state.scene_plan):
            self.log_progress(f"Creating audio for scene {i+1}/{len(state.scene_plan)}")
            # Pass the isolated directory
            audio_path = self._generate_audio(scene, i, run_audio_dir)
            audio_files.append(str(audio_path))
        
        state.audio_files = audio_files
        self.log_progress(f"Generated {len(audio_files)} audio files")
        
        return state
    
    def _generate_audio(self, scene: Dict[str, Any], scene_index: int, cache_dir: Path) -> Path:
        """
        Generate audio with Speed Control and SSML Pause support.
        """
        import imageio_ffmpeg
        import subprocess
        from moviepy import AudioFileClip, concatenate_audioclips
        import time  # For retry backoff
        import re
        import os
        
        narration_text = scene.get('narration_text', '')
        # Sanitize text but keep <break> tags
        narration_text = self._sanitize_text_for_tts(narration_text, keep_ssml=True)
        
        if not narration_text.strip():
            return self._create_silent_audio(scene.get('duration', 10), scene_index)
            
        final_output_path = cache_dir / f"audio_{scene_index:03d}.mp3"
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        # 1. Parse Segments (Text vs Break)
        # Regex to find <break time="500ms"/>
        segments = re.split(r'(<break\s+time="(\d+)ms"\s*/>)', narration_text)
        
        audio_clips = []
        
        # Iterating: segments[0]=text, segments[1]=tag, segments[2]=time, segments[3]=text...
        i = 0
        while i < len(segments):
            text_part = segments[i]
            i += 1
            
            # If it's the time capture group (digit), skip (already handled by tag check)
            if text_part and text_part.isdigit() and i < len(segments) and segments[i-2].startswith('<break'):
                continue
                
            # Check if this part was a break tag
            if text_part and text_part.startswith('<break'):
                # Extract time from next captured group if regex logic holds, 
                # OR just parse the tag string directly simpler
                match = re.search(r'time="(\d+)ms"', text_part)
                if match:
                    ms = int(match.group(1))
                    audio_clips.append(self._create_silent_clip(ms / 1000.0))
                continue
            
            # Otherwise it's text
            if text_part and text_part.strip():
                # Clean specific punctuation for gTTS
                clean_text = self._sanitize_text_for_tts(text_part, keep_ssml=False)
                if not clean_text.strip():
                    continue
                    
                # Generate Raw Audio
                raw_path = cache_dir / f"temp_raw_{scene_index}_{i}.mp3"
                
                if self.engine == 'edge-tts':
                    # Edge TTS (CLI) - High Quality Neural Voice
                    # RETRY LOGIC ADDED to prevent falling back to female voice on transient errors
                    success = False
                    for attempt in range(3):
                        try:
                            subprocess.run([
                                'edge-tts',
                                '--text', clean_text,
                                '--write-media', str(raw_path),
                                '--voice', self.voice
                            ], check=True, capture_output=True)
                            success = True
                            break
                        except subprocess.CalledProcessError as e:
                            self.log_progress(f"Edge TTS attempt {attempt+1} failed: {e.stderr}", level="warning")
                            time.sleep(1 * (attempt+1))
                        except FileNotFoundError:
                             self.log_progress("edge-tts binary not found. Is it installed?", level="error")
                             # No point retrying if binary missing
                             break
                    
                    if not success:
                         self.log_progress(f"Edge TTS failed after 3 attempts. Falling back to gTTS.", level="error")
                         tts = gTTS(text=clean_text, lang='en', slow=False)
                         tts.save(str(raw_path))
                else:
                    # Standard gTTS
                    tts = gTTS(text=clean_text, lang='en', slow=False)
                    tts.save(str(raw_path))
                
                # Apply Speed (1.05x) using ffmpeg 'atempo'
                # Apply Speed (1.05x) using ffmpeg 'atempo'
                # User asked for faster narration (Brisk News).
                slow_path = cache_dir / f"temp_slow_{scene_index}_{i}.mp3"
                cmd = [
                    ffmpeg_exe, '-y', '-v', 'error',
                    '-i', str(raw_path),
                    '-filter:a', 'atempo=1.05',
                    '-vn', str(slow_path)
                ]
                subprocess.run(cmd, check=True)
                
                # Load as MoviePy Clip
                try:
                    clip = AudioFileClip(str(slow_path))
                    audio_clips.append(clip)
                except Exception as e:
                    self.log_progress(f"Error loading clip: {e}", level="error")

        if not audio_clips:
             return self._create_silent_audio(scene.get('duration', 5), scene_index)

        # 2. Concatenate
        files_to_close = audio_clips
        try:
            final_clip = concatenate_audioclips(audio_clips)
            final_clip.write_audiofile(str(final_output_path), logger=None, fps=44100)
            final_clip.close()
        except Exception as e:
            self.log_progress(f"Concat error: {e}", level="error")
            # Fallback: just return first clip or silent
            return self._create_silent_audio(5, scene_index)
        finally:
             for c in files_to_close:
                 if hasattr(c, 'close'): c.close()
        
        return final_output_path

    def _create_silent_clip(self, duration_sec: float):
        from moviepy import AudioArrayClip
        import numpy as np
        # 44100Hz silence
        silence = np.zeros((int(duration_sec * 44100), 2))
        return AudioArrayClip(silence, fps=44100)
        
    def _create_silent_audio(self, duration: float, scene_index: int) -> Path:
        path = self.temp_dir / f"audio_{scene_index}_silent.mp3"
        clip = self._create_silent_clip(duration)
        clip.write_audiofile(str(path), fps=44100, logger=None)
        clip.close()
        return path

    def _sanitize_text_for_tts(self, text: str, keep_ssml: bool = False) -> str:
        """
        Clean text to ensure natural pronunciation and remove artifacts.
        """
        import re
        
        if not text:
            return ""
            
        # Remove markdown bold/italic
        text = text.replace('**', '').replace('*', '')
        
        # Remove brackets and things inside them (often stage directions)
        # BUT preserve <break> tags if requested
        if keep_ssml:
             # Temporarily hide break tags
             placeholders = []
             def replace_break(match):
                 placeholders.append(match.group(0))
                 return f"__SSML_BREAK_{len(placeholders)-1}__"
             
             text = re.sub(r'<break.*?>', replace_break, text)
             
             # Clean brackets
             text = re.sub(r'\[.*?\]', '', text)
             text = re.sub(r'\(.*?\)', '', text)
             
             # Restore break tags
             for i, tag in enumerate(placeholders):
                 text = text.replace(f"__SSML_BREAK_{i}__", tag)
        else:
             text = re.sub(r'\[.*?\]', '', text)
             text = re.sub(r'\(.*?\)', '', text)
        
        # Remove "News Anchor:" prefixes if they snuck in
        text = re.sub(r'^(News Anchor|Host|Narrator):\s*', '', text, flags=re.IGNORECASE)
        
        # Replace complex punctuation with simple pauses
        text = text.replace(' -- ', ', ').replace('—', ', ')
        
        # Ensure single spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
