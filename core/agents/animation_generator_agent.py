"""
Animation Generator Agent
Renders visual scenes into video clips with news-style lower thirds
"""

from typing import Dict, Any
from pathlib import Path
import os

from moviepy import ImageClip, CompositeVideoClip, ColorClip, VideoFileClip, vfx

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .video_generator_agent import VideoGeneratorAgent
from .base_agent import AgentState


class AnimationGeneratorAgent(VideoGeneratorAgent):
    """Generates animated video clips with lower-thirds captions."""

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def execute(self, state: AgentState) -> AgentState:
        if not self.validate_input(state, ["scene_plan"]):
            return state

        self.log_progress("Generating animated scene clips with lower-thirds")

        scene_clips = []
        for idx, scene in enumerate(state.scene_plan):
            self.log_progress(f"Rendering scene {idx + 1}/{len(state.scene_plan)}")
            # Enforce idx as int
            clip_path = self._render_scene(scene, int(idx), state.topic)
            scene_clips.append(str(clip_path))

        state.scene_clips = scene_clips
        self.log_progress(f"Generated {len(scene_clips)} scene clips")

        return state

    # ---------------------------------------------------------
    # Core rendering logic
    # ---------------------------------------------------------

    def _render_scene(self, scene: Dict[str, Any], idx: int, topic: str) -> Path:
        """
        Render a single scene with Advanced Ken Burns, Dark Overlay, and Broadcast Lower Thirds.
        """
        # 1. Prepare Base Image
        image_path = scene.get("visual_assets", {}).get("image_path")
        if not image_path or not os.path.exists(image_path):
            # Fallback black clip
            return ColorClip(size=self.resolution, color=(0,0,0), duration=scene['duration'])

        # Check for Video (Wan 2.2)
        if image_path and image_path.lower().endswith(".mp4"):
            # Use VideoFileClip for generated video
            bg_clip = VideoFileClip(image_path)
            
            # 1. Loop or Trim to match scene duration
            if bg_clip.duration < scene['duration']:
                # Loop video to fill duration
                # Use vfx.Loop (available in moviepy v2 commonly as built-in or effect)
                # Or just Loop manually if vfx.Loop is tricky. 
                # Let's try explicit loop or just time-based resize
                # Safe way: concatenate itself?
                 bg_clip = bg_clip.with_effects([vfx.Loop(duration=scene['duration'])])
            else:
                 bg_clip = bg_clip.with_subclip(0, scene['duration'])
                 
            # 2. Resize to Cover
            # Wan generates 16:9 usually, so fit to width/height
            img_w, img_h = bg_clip.size
            screen_w, screen_h = self.resolution
            ratio = max(screen_w / img_w, screen_h / img_h)
            bg_clip = bg_clip.resized(ratio).with_position("center")
            
        else:
            # Load and Resize Image (Cover)
            img_clip = ImageClip(image_path).with_duration(scene['duration'])
            
            # Scale to fill (like CSS cover)
            img_w, img_h = img_clip.size
            screen_w, screen_h = self.resolution
            
            ratio = max(screen_w / img_w, screen_h / img_h)
            # Add 15% buffer for Ken Burns movement
            ratio *= 1.15  
            img_clip = img_clip.resized(ratio)

            # 2. Apply Motion (Ken Burns Variants)
            motion_type = scene.get("visual", {}).get("camera_motion", "zoom_in")
            bg_clip = self._apply_motion(img_clip, motion_type, scene['duration'])
            bg_clip = bg_clip.with_position("center")

        # 3. Add Dark Overlay (Cinematic Depth)
        # 3. Add Dark Overlay (Cinematic Depth)
        # Fix: Use explicit NumPy array instead of ColorClip to avoid broadcasting errors
        screen_w, screen_h = self.resolution
        overlay_array = np.zeros((screen_h, screen_w, 4), dtype=np.uint8)
        overlay_array[:] = [0, 0, 0, int(255 * 0.15)] # 15% opacity
        
        overlay = ImageClip(overlay_array).with_duration(scene['duration'])

        # 4. Add Broadcast Lower Thirds
        # Only if text exists
        lower_third_text = (
            scene.get("visual", {}).get("lower_third_text")
            or scene.get("on_screen_text", "")
        )
        composites = [bg_clip, overlay]
        
        if lower_third_text:
             lower_third_clips = self._create_lower_third(lower_third_text, scene.get('location', ''), scene['duration'])
             composites.extend(lower_third_clips)
             
        # 5. Composite Final Scene
        # MoviePy v2: use with_effects for FadeIn/FadeOut
        effects = [vfx.FadeIn(0.5), vfx.FadeOut(0.5)]
        
        final_clip = CompositeVideoClip(
            composites,
            size=self.resolution
        ).with_effects(effects)

        output_path = self.temp_dir / f"scene_{idx:03d}.mp4"
        final_clip.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio=False,
            logger=None
        )

        final_clip.close()
        return output_path

    def _apply_motion(self, clip: ImageClip, motion_type: str, duration: float) -> ImageClip:
        """
        Apply news-style Ken Burns effects.
        """
        # We assume the clip is already 1.15x larger than screen
        
        if motion_type == 'zoom_in':
            # Medium-Fast zoom (0.07 factor) - User Request 175%
            return clip.with_effects([vfx.Resize(lambda t: 1 + 0.07 * (t / duration))])
            
        elif motion_type == 'zoom_out':
            # Medium-Fast reveal
            return clip.with_effects([vfx.Resize(lambda t: 1.10 - 0.07 * (t / duration))])
            
        elif motion_type == 'pan_left':
            # Move Right to Left (Medium: 60px)
            return clip.with_position(lambda t: (int(-60 * (t / duration)), "center"))
            
        elif motion_type == 'pan_right':
            # Move Left to Right (Medium: 60px)
            return clip.with_position(lambda t: (int(60 * (t / duration)), "center"))
            
        # Default: Gentle Zoom
        return clip.with_effects([vfx.Resize(lambda t: 1 + 0.05 * (t / duration))])

    # ---------------------------------------------------------
    # Background helpers
    # ---------------------------------------------------------

    def _image_background(self, image_path: str, duration: int, scene_type: str = "INFOGRAPHIC"):
        """Background with dynamic Ken Burns or Shake based on scene type."""
        # Load and resize to cover screen (maintain aspect ratio to avoid black bars)
        # Note: We resize to Height + 20% to allow for pan/shake room
        h = int(self.resolution[1] * 1.2)
        clip = ImageClip(image_path).resized(height=h).with_duration(duration)
        
        # Center crop to screen size initially
        clip = clip.with_position("center")

        # Effect 1: Ken Burns (Zoom)
        # Re-enactments get aggressive zoom, others get subtle
        zoom_speed = 0.08 if scene_type == "RE_ENACTMENT" else 0.03
        
        # Effect 1: Ken Burns (Zoom)
        zoom_clip = clip.resized(lambda t: 1 + zoom_speed * t)

        # Effect 2: Camera Shake - DISABLED
        
        return zoom_clip.with_position("center")

    # ---------------------------------------------------------
    # Lower-third helpers
    # ---------------------------------------------------------

    def _create_text_clip(self, text, fontsize, color, font="arial.ttf", size=None, position=None):
        """Creates a MoviePy ImageClip from text using PIL, bypassing ImageMagick."""
        # Create a dummy image to calculate text size
        dummy_img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy_img)
        
        try:
             font_obj = ImageFont.truetype(font, fontsize)
        except OSError:
            try:
                # Try absolute path for Windows common font
                font_obj = ImageFont.truetype("arial.ttf", fontsize)
            except OSError:
                 font_obj = ImageFont.load_default()

        # Calculate text size
        try:
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font_obj)
            text_w, text_h = right - left, bottom - top
        except AttributeError:
            text_w, text_h = draw.textsize(text, font=font_obj)

        # Enforce minimums and even dimensions
        width = max(text_w + 20, 100)
        height = max(text_h + 20, 50)
        
        # Make even
        if width % 2 != 0: width += 1
        if height % 2 != 0: height += 1

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), text, font=font_obj, fill=color)

        # Convert to numpy array for MoviePy
        img_np = np.array(img)
        
        # FIX: Return simple RGBA ImageClip. 
        # MoviePy will handle the alpha channel automatically for mixing.
        # Separating mask manually caused broadcasting errors in v2.
        clip = ImageClip(img_np)
        
        if position:
            clip = clip.with_position(position)
            
        return clip

    def _create_lower_third(self, headline: str, subtext: str, duration: int):
        """
        Generate Lower Third as a SINGLE ImageClip (Safety Mode).
        Combines background bar and text into one RGBA image to avoid MoviePy compositing errors.
        """
        screen_w, screen_h = self.resolution
        
        # Dimensions
        bar_height = int(screen_h * 0.18)
        bar_w = int(screen_w)
        
        # Create a single PIL Image for the graphical element
        # Size: Full width, fixed height (enough for bar)
        img_h = bar_height + 50
        l3_img = Image.new('RGBA', (bar_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(l3_img)
        
        # 1. Draw Bar
        draw.rectangle(
            [(0, 0), (bar_w, bar_height)],
            fill=(0, 0, 0, int(255 * 0.85))
        )
        
        # 2. Draw Text (Headline)
        try:
             font_head = ImageFont.truetype("arial.ttf", 40)
        except:
             font_head = ImageFont.load_default()
             
        draw.text((100, 20), headline[:48], font=font_head, fill="white")
        
        # 3. Draw Subtext
        if subtext:
            try:
                font_sub = ImageFont.truetype("arial.ttf", 24)
            except:
                font_sub = ImageFont.load_default()
            draw.text((100, bar_height - 40), subtext[:40], font=font_sub, fill="#FF4444")
            
        # Convert to MoviePy
        l3_np = np.array(l3_img)
        l3_clip = ImageClip(l3_np).with_duration(duration)
        
        # Animation: Slide Up
        target_y = screen_h - bar_height - 50
        start_y = screen_h
        
        def slide_pos(t):
            anim_time = 0.8
            if t < 0: return ("center", int(start_y))
            if t >= anim_time: return ("center", int(target_y))
            
            # Ease Out
            progress = t / anim_time
            ease = 1 - pow(1 - progress, 3)
            curr = start_y - ((start_y - target_y) * ease)
            return ("center", int(curr))
            
        l3_clip = l3_clip.with_position(slide_pos)
        
        return [l3_clip]
