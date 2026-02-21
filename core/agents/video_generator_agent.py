"""Base Video Generator Agent - Common utilities for video generation."""

from typing import Dict, Any, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from .base_agent import BaseAgent


class VideoGeneratorAgent(BaseAgent):
    """Base class for video generation agents with common utilities."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.video_config = config.get('video', {})
        self.animation_config = config.get('animation', {})
        self.paths_config = config.get('paths', {})
        
        # Video settings
        self.fps = self.animation_config.get('fps', 30)
        self.resolution = self._parse_resolution(
            self.animation_config.get('resolution', '1080p')
        )
        self.bg_color = self.video_config.get('background_color', '#1a1a2e')
        self.text_color = self.video_config.get('text_color', '#FFFFFF')
        self.accent_color = self.video_config.get('highlight_color', '#00d4ff')
        
        # Paths
        self.output_dir = Path(self.paths_config.get('output_dir', 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(self.paths_config.get('temp_dir', 'temp'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    
    def _parse_resolution(self, resolution: str) -> Tuple[int, int]:
        """
        Parse resolution string to (width, height).
        
        Args:
            resolution: Resolution string like '1080p', '720p', '4k'
            
        Returns:
            Tuple of (width, height)
        """
        resolutions = {
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '4k': (3840, 2160)
        }
        return resolutions.get(resolution, (1920, 1080))
    
    def _hex_to_rgb(self, hex_color: str, default="#FFFFFF") -> Tuple[int, int, int]:
        """
        Safely convert hex color (#RRGGBB) to RGB.
        Never throws ValueError.
        """
        if not isinstance(hex_color, str) or not hex_color.strip():
            hex_color = default

        hex_color = hex_color.strip().lstrip("#")

        # Support shorthand like #fff
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)

        if len(hex_color) != 6:
            hex_color = default.lstrip("#")

        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return (255, 255, 255)

    
    def create_text_image(
        self,
        text: str,
        font_size: int = 60,
        color: str = None,
        max_width: int = None
    ) -> Image.Image:
        """
        Create an image with text.
        
        Args:
            text: Text to render
            font_size: Font size in pixels
            color: Text color (hex), defaults to config text_color
            max_width: Maximum width for text wrapping
            
        Returns:
            PIL Image with text
        """
        width, height = self.resolution
        color = color or self.text_color or "#FFFFFF"
        rgb_color = self._hex_to_rgb(color)

        
        # Create image
        img = Image.new('RGB', (width, height), self._hex_to_rgb(self.bg_color))
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Word wrap if needed
        if max_width:
            text = self._wrap_text(text, font, max_width, draw)
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, font=font, fill=rgb_color)
        
        return img
    
    def _wrap_text(
        self,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
        draw: ImageDraw.ImageDraw
    ) -> str:
        """
        Wrap text to fit within max_width.
        
        Args:
            text: Text to wrap
            font: Font to use
            max_width: Maximum width in pixels
            draw: ImageDraw object for measuring
            
        Returns:
            Wrapped text with newlines
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def create_gradient_background(
        self,
        color1: str = None,
        color2: str = None,
        vertical: bool = True
    ) -> Image.Image:
        """
        Create a gradient background image.
        
        Args:
            color1: Start color (hex)
            color2: End color (hex)
            vertical: True for vertical gradient, False for horizontal
            
        Returns:
            PIL Image with gradient
        """
        width, height = self.resolution
        color1 = color1 or self.bg_color
        color2 = color2 or self.accent_color
        
        rgb1 = self._hex_to_rgb(color1)
        rgb2 = self._hex_to_rgb(color2)
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create gradient
        if vertical:
            for y in range(height):
                ratio = y / height
                r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
                g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
                b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        else:
            for x in range(width):
                ratio = x / width
                r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
                g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
                b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))
        
        return img
    
    def cleanup_temp_files(self, pattern: str = "*"):
        """
        Clean up temporary files.
        
        Args:
            pattern: Glob pattern for files to delete
        """
        for file in self.temp_dir.glob(pattern):
            try:
                file.unlink()
                self.log_progress(f"Cleaned up: {file.name}", level="debug")
            except Exception as e:
                self.log_progress(f"Failed to delete {file.name}: {e}", level="warning")
