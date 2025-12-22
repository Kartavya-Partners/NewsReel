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
        
        self.log_progress("Generating voiceover audio")
        
        audio_files = []
        
        for i, scene in enumerate(state.scene_plan):
            self.log_progress(f"Creating audio for scene {i+1}/{len(state.scene_plan)}")
            audio_path = self._generate_audio(scene, i)
            audio_files.append(str(audio_path))
        
        state.audio_files = audio_files
        self.log_progress(f"Generated {len(audio_files)} audio files")
        
        return state
    
    def _generate_audio(self, scene: Dict[str, Any], scene_index: int) -> Path:
        """
        Generate audio file for a single scene.
        
        Args:
            scene: Scene dictionary with narration_text
            scene_index: Index of the scene
            
        Returns:
            Path to generated audio file
        """
        narration_text = scene.get('narration_text', '')
        
        if not narration_text.strip():
            self.log_progress(f"Scene {scene_index} has no narration text", level="warning")
            # Create silent audio placeholder
            return self._create_silent_audio(scene.get('duration', 10), scene_index)
        
        # Check cache first
        cache_key = self._get_cache_key(narration_text)
        cached_path = self.audio_cache_dir / f"{cache_key}.mp3"
        
        if cached_path.exists():
            self.log_progress(f"Using cached audio for scene {scene_index}", level="debug")
            # Copy to scene-specific name
            output_path = self.temp_dir / f"audio_{scene_index:03d}.mp3"
            import shutil
            shutil.copy(cached_path, output_path)
            return output_path
        
        # Generate new audio
        output_path = self.temp_dir / f"audio_{scene_index:03d}.mp3"
        
        try:
            if self.engine == 'gtts':
                tts = gTTS(text=narration_text, lang='en', slow=False)
                tts.save(str(output_path))
                
                # Save to cache
                import shutil
                shutil.copy(output_path, cached_path)
            else:
                # Fallback to pyttsx3 if available
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', int(150 * self.speed))
                    engine.save_to_file(narration_text, str(output_path))
                    engine.runAndWait()
                except ImportError:
                    self.log_progress(
                        "Neither gTTS nor pyttsx3 available, creating silent audio",
                        level="warning"
                    )
                    return self._create_silent_audio(scene.get('duration', 10), scene_index)
        
        except Exception as e:
            self.log_progress(f"Error generating audio: {e}", level="error")
            return self._create_silent_audio(scene.get('duration', 10), scene_index)
        
        return output_path
    
    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.
        
        Args:
            text: Text to hash
            
        Returns:
            MD5 hash of text
        """
        return hashlib.md5(text.encode()).hexdigest()
    
    def _create_silent_audio(self, duration: float, scene_index: int) -> Path:
        """
        Create a silent audio file as fallback.
        
        Args:
            duration: Duration in seconds
            scene_index: Scene index
            
        Returns:
            Path to silent audio file
        """
        from moviepy.editor import AudioClip
        import numpy as np
        
        output_path = self.temp_dir / f"audio_{scene_index:03d}_silent.mp3"
        
        # Create silent audio
        silent_audio = AudioClip(
            lambda t: np.zeros(2),  # Stereo silence
            duration=duration,
            fps=44100
        )
        
        silent_audio.write_audiofile(
            str(output_path),
            fps=44100,
            verbose=False,
            logger=None
        )
        
        return output_path
