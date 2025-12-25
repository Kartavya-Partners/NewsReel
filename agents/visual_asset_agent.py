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
                scene_type = scene.get('visual', {}).get('scene_type', 'INFOGRAPHIC')
                
                image_path = None
                source = "generated"
                backup_real_path = None
                
                # STRATEGY 1: Real News Image (ONLY for REAL_FOOTAGE)
                if scene_type == 'REAL_FOOTAGE' and real_images and idx < len(real_images):
                    try:
                        target_url = real_images[idx % len(real_images)]
                        # Tuple unpacking: (main_path, backup_path)
                        result_path, backup = self._fetch_real_image(target_url, idx)
                        
                        if result_path:
                             image_path = result_path
                             source = "real_news"
                        elif backup:
                             # Main failed (too small), but backup exists
                             backup_real_path = backup
                             self.log_progress(f"Scene {idx+1}: Real image small. Saved as backup.", level="info")
                    except Exception as e:
                        self.log_progress(f"Real image failed: {e}", level="warning")
                
                # STRATEGY 2: AI Generation (Primary)
                if not image_path:
                    query = scene.get("visual", {}).get("image_query", "")
                    if not query or len(query) < 10:
                        query = f"News illustration of {scene.get('location', 'event')}, digital art"
                    
                    # Force Quality & No Text (User Feedback: "Images not good")
                    query += ", no text, no typography, 8k, masterpiece, detailed, photorealistic"
                    
                    try:
                         image_path = self._fetch_pollinations_image(query)
                         source = "generated_pollinations"
                    except RuntimeError:
                        self.log_progress(f"Scene {idx+1}: AI Gen detailed failed. Retrying simplified...", level="warning")
                        # STRATEGY 3: AI Generation (Simplified Retry)
                        # Strip complex params (after "STYLE:")
                        simple_query = query.split(", STYLE:")[0] + ", photo"
                        try:
                            image_path = self._fetch_pollinations_image(simple_query)
                            source = "generated_pollinations_simple"
                        except Exception:
                            self.log_progress(f"Scene {idx+1}: AI Gen simple failed.", level="error")

                # STRATEGY 4: Low-Res Real Image Recovery
                if not image_path and backup_real_path:
                    try:
                        self.log_progress(f"Scene {idx+1}: Recovering Low-Res Backup...", level="info")
                        image_path = self._generate_upscaled_composite(backup_real_path, idx)
                        source = "real_news_recovered"
                    except Exception as e:
                         self.log_progress(f"Backup recovery failed: {e}", level="error")

                # STRATEGY 5: Text Fallback (Last Resort)
                if not image_path:
                    raise RuntimeError("All visual strategies failed.")

                scene["visual_assets"] = {
                    "image_path": str(image_path),
                    "source": source
                }
            except Exception as e:
                # Dynamic Fallback: Generate a text slide
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

    def _generate_upscaled_composite(self, small_img_path: Path, idx: int) -> Path:
        """
        Recover a small image by creating a TV-style blurred background composite.
        """
        from PIL import Image, ImageFilter, ImageEnhance
        
        output_path = self.asset_dir / f"recovered_{idx}.jpg"
        target_size = (1280, 720)
        
        try:
            with Image.open(small_img_path) as original:
                # 1. Background: Resize original to Cover screen & Blur
                bg = original.resize(target_size, Image.Resampling.LANCZOS)
                bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
                # Darken background
                enhancer = ImageEnhance.Brightness(bg)
                bg = enhancer.enhance(0.5)
                
                # 2. Foreground: Resize original to fit nicely (keep aspect ratio)
                # Max height 80% (576px)
                aspect = original.width / original.height
                new_h = int(720 * 0.8)
                new_w = int(new_h * aspect)
                
                fg = original.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # 3. Composite centering
                x = (1280 - new_w) // 2
                y = (720 - new_h) // 2
                
                # Paste foreground
                bg.paste(fg, (x, y))
                
                bg.save(output_path)
                return output_path
        except Exception as e:
            raise RuntimeError(f"Composite failed: {e}")

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
                         # DO NOT DELETE. Rename to backup.
                         backup_path = self.asset_dir / f"backup_real_{key}.jpg"
                         if image_path.exists():
                             image_path.replace(backup_path)
                         # Return None to signal "Main image failed", but backup exists
                         return None, backup_path
                     
                     return image_path, None
             except Exception as e:
                 if image_path.exists():
                     image_path.unlink()
                 raise e

             return None, None
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
        
        # Increased timeout to 120s (User Request)
        # Retry logic: 3 attempts
        import time
        from PIL import Image, UnidentifiedImageError
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=120)
                if response.status_code == 200:
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                        
                    # Validate Image Integrity immediately
                    try:
                        with Image.open(image_path) as img:
                            img.verify() # Check for corruption
                        return image_path
                    except Exception as img_err:
                        self.log_progress(f"Generated image corrupt: {img_err}", level="warning")
                        if image_path.exists(): image_path.unlink()
                        continue # Retry
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
