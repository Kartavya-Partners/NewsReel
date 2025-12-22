"""
Animation Generator Agent
Creates video clips for each scene using MoviePy + PIL-generated images.
"""

from typing import Dict, Any
from pathlib import Path

import numpy as np
from moviepy.video.VideoClip import ImageClip

from .video_generator_agent import VideoGeneratorAgent
from .base_agent import AgentState


class AnimationGeneratorAgent(VideoGeneratorAgent):
    """Agent responsible for generating scene animations."""

    def execute(self, state: AgentState) -> AgentState:
        """
        Generate video clips for each scene.

        Args:
            state: Current agent state with scene_plan

        Returns:
            Updated state with scene_clips (list of file paths)
        """
        if not self.validate_input(state, ["scene_plan"]):
            return state

        self.log_progress("Generating scene animations")

        scene_clips = []

        for i, scene in enumerate(state.scene_plan):
            self.log_progress(
                f"Creating animation for scene {i + 1}/{len(state.scene_plan)}"
            )
            clip_path = self._create_scene_clip(scene, i)
            scene_clips.append(str(clip_path))

        state.scene_clips = scene_clips
        self.log_progress(f"Generated {len(scene_clips)} scene animations")

        return state

    def _create_scene_clip(self, scene: Dict[str, Any], scene_index: int) -> Path:
        """
        Create a video clip for a single scene.

        Args:
            scene: Scene dictionary with narration_text, on_screen_text, etc.
            scene_index: Index of the scene

        Returns:
            Path to generated clip file
        """
        duration = scene.get("duration", 10)
        visual_type = scene.get("visual_type", "content")
        on_screen_text = scene.get(
            "on_screen_text",
            scene.get("narration_text", "")
        )

        # ---- Background selection based on visual type ----
        if visual_type == "headline":
            bg_img = self.create_gradient_background(
                color1="#1a1a2e",
                color2="#16213e",
                vertical=True
            )
            font_size = 80
        elif visual_type == "conclusion":
            bg_img = self.create_gradient_background(
                color1="#16213e",
                color2="#0f3460",
                vertical=True
            )
            font_size = 70
        elif visual_type == "data":
            bg_img = self.create_gradient_background(
                color1="#0f3460",
                color2="#16213e",
                vertical=False
            )
            font_size = 60
        else:  # content
            bg_img = self.create_gradient_background(
                color1="#1a1a2e",
                color2="#0f3460",
                vertical=True
            )
            font_size = 65

        # ---- Text styling (config-driven defaults) ----
        text_color = scene.get(
            "text_color",
            self.config["video"].get("text_color", "#FFFFFF")
        )

        text_img = self.create_text_image(
            text=on_screen_text,
            font_size=font_size,
            max_width=int(self.resolution[0] * 0.8),
            color=text_color
        )

        # ---- Convert PIL images to NumPy arrays ----
        bg_array = np.array(bg_img)
        text_array = np.array(text_img)

        # ---- Safe background color for masking ----
        bg_color = self.config["video"].get("background_color", "#0F172A")
        bg_color_rgb = self._hex_to_rgb(bg_color)

        # Create mask where text pixels are present
        text_mask = ~np.all(text_array == bg_color_rgb, axis=2)

        # Composite background + text
        final_array = bg_array.copy()
        final_array[text_mask] = text_array[text_mask]

        # ---- Create MoviePy clip ----
        clip = ImageClip(final_array).set_duration(duration)
        clip = clip.fadein(0.5).fadeout(0.5)

        # ---- Save clip ----
        output_path = self.temp_dir / f"scene_{scene_index:03d}.mp4"
        clip.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio=False,
            verbose=False,
            logger=None
        )

        return output_path
