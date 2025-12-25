"""
Visual Asset Agent - Retrieves or generates visual assets for scenes.
"""

from typing import Dict, Any
from pathlib import Path
import requests
import hashlib
from .base_agent import BaseAgent, AgentState


class VisualAssetAgent(BaseAgent):
    """Fetches images for scenes based on visual plans."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.asset_dir = Path("temp/images")
        self.asset_dir.mkdir(parents=True, exist_ok=True)

        self.fallback_image = Path("assets/placeholders/news_generic.jpg")
        self.fallback_image.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure fallback image actually exists
        if not self.fallback_image.exists():
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1280, 720), color=(20, 20, 30))
            d = ImageDraw.Draw(img)
            d.text((10,10), "News Fallback", fill=(255,255,255))
            img.save(self.fallback_image)

    def execute(self, state: AgentState) -> AgentState:
        if not self.validate_input(state, ["scene_plan"]):
            return state

        self.log_progress("Fetching visual assets")
        
        # --- Collect Real Images from News Articles ---
        real_images = []
        if state.raw_articles:
            for article in state.raw_articles:
                img_url = article.get('image_url')
                if img_url and img_url.startswith('http'):
                    real_images.append(img_url)
        
        self.log_progress(f"Found {len(real_images)} real news images")

        for idx, scene in enumerate(state.scene_plan):
            try:
                # Decide based on Scene Type
                scene_type = scene.get('visual', {}).get('scene_type', 'INFOGRAPHIC')
                visual_style = scene.get('visual', {}).get('visual_style', '3d_render')
                
                image_path = None
                source = "generated"
                
                # STRATEGY 1: Real News Image (ONLY for REAL_FOOTAGE)
                if scene_type == 'REAL_FOOTAGE' and real_images and idx < len(real_images):
                    try:
                        target_url = real_images[idx % len(real_images)]
                        image_path = self._fetch_real_image(target_url, idx)
                        source = "real_news"
                    except Exception as e:
                        self.log_progress(f"Real image rejected/failed: {e}, falling back to generation")
                
                # STRATEGY 2: Generate via Pollinations (Re-enactment or Fallback)
                if not image_path:
                    query = scene.get("visual", {}).get("image_query", "")
                    
                    # Ensure query is robust if it came empty
                    if not query or len(query) < 10:
                        query = f"News illustration of {scene.get('location', 'event')}, digital art"

                    image_path = self._fetch_pollinations_image(query)
                    source = "generated_pollinations"

                scene["visual_assets"] = {
                    "image_path": str(image_path),
                    "source": source
                }
            except Exception as e:
                # Dynamic Fallback: Generate a text slide instead of generic placeholder
                fallback_path = self._generate_dynamic_fallback(scene, idx)
                scene["visual_assets"] = {
                    "image_path": str(fallback_path),
                    "source": "fallback_dynamic"
                }
                self.log_progress(
                    f"Generated dynamic fallback for scene {idx + 1}: {e}",
                    level="warning"
                )

        self.log_progress("Visual assets attached")
        return state

    def _generate_dynamic_fallback(self, scene: Dict[str, Any], idx: int) -> Path:
        """Generate a simple text slide when AI generation fails."""
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = (1280, 720) # Default HD
        
        # 1. Dark Background
        img = Image.new('RGB', (width, height), color='#111122')
        draw = ImageDraw.Draw(img)
        
        # 2. Text Content
        text = scene.get("visual", {}).get("lower_third_text") or \
               scene.get("on_screen_text") or \
               f"Scene {idx + 1}"
               
        # Truncate
        if len(text) > 50:
            text = text[:47] + "..."
            
        # 3. Draw Text (Centered)
        try:
            # Try to load a font, or use default
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            # Use textbbox if available (Pillow >= 10)
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            else:
                text_w, text_h = draw.textsize(text, font=font)
                
            x = (width - text_w) / 2
            y = (height - text_h) / 2
            
            draw.text((x, y), text, font=font, fill='white')
            
        except Exception as e:
            print(f"Fallback font error: {e}")
            
        # 4. Save
        output_path = self.asset_dir / f"fallback_{idx}.jpg"
        img.save(output_path)
        return output_path

    # --------------------------------------------------------

    def _fetch_real_image(self, url: str, idx: int) -> Path:
        """Download a real image from a URL."""
        import hashlib
        key = hashlib.md5(url.encode()).hexdigest()
        image_path = self.asset_dir / f"real_{key}.jpg"
        
        if image_path.exists():
            return image_path
            
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
             with open(image_path, "wb") as f:
                f.write(response.content)
             
             # Validate Image Size
             try:
                 from PIL import Image
                 with Image.open(image_path) as img:
                     width, height = img.size
                     if width < 800 or height < 600:
                         image_path.unlink()
                         raise RuntimeError(f"Image too small ({width}x{height})")
             except Exception as e:
                 if image_path.exists():
                     image_path.unlink()
                 raise e

             return image_path
        raise RuntimeError(f"Status {response.status_code}")

    def _fetch_pollinations_image(self, query: str) -> Path:
        import hashlib
        key = hashlib.md5(query.encode()).hexdigest()
        image_path = self.asset_dir / f"gen_{key}.jpg"

        if image_path.exists():
            return image_path

        # Use Pollinations.ai as a reliable, free generative source
        # Encode query to be URL safe
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://image.pollinations.ai/prompt/{encoded_query}?width=1280&height=720&nologo=true"
        
        # Increased timeout to 60s for slow generation
        # Retry logic: 3 attempts
        import time
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    return image_path
                else:
                    self.log_progress(f"Pollinations attempt {attempt+1} failed: {response.status_code}", level="warning")
            except requests.exceptions.RequestException as e:
                self.log_progress(f"Pollinations attempt {attempt+1} error: {e}", level="warning")
            
            if attempt < 2:
                time.sleep(2 * (attempt + 1)) # Backoff: 2s, 4s

        raise RuntimeError("Pollinations generation failed after 3 attempts")

    def _resolve_scene_image(self, scene: Dict[str, Any]) -> Path:
        # Legacy method kept for interface compatibility if needed, but logic moved to execute
        pass
