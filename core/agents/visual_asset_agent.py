"""
Visual Asset Agent - Retrieves or generates visual assets for scenes.
"""

from typing import Dict, Any
from pathlib import Path
import requests
import hashlib
import os
from .base_agent import BaseAgent, AgentState
from ..utils.wan_client import WanClient # New Import


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

        # Initialize WanClient if enabled
        # Initialize WanClient if enabled
        self.wan_client = None
        gen_config = self.config.get("video", {}).get("generation", {})
        
        if gen_config.get("enable"):
             provider = gen_config.get("provider", "piapi")
             
             if provider == "local":
                 self.wan_client = WanClient(
                     mode="local",
                     model=gen_config.get("model", "wan-2.1-14b"),
                     local_paths={
                         "repo": gen_config.get("local_wan_path", "../Wan-Video"),
                         "checkpoint": gen_config.get("local_checkpoint_path", "./weights/Wan2.2-I2V-14B-720P-INT8")
                     }
                 )
                 self.log_progress(f"Wan 2.2 Local Video Generation Enabled (Model: {self.wan_client.model})")
             
             elif provider == "piapi":
                 api_key = gen_config.get("api_key")
                 # Resolve env var if needed
                 if api_key and api_key.startswith("${"):
                     env_var = api_key[2:-1]
                     api_key = os.getenv(env_var)
                 
                 if api_key:
                     self.wan_client = WanClient(
                         api_key=api_key, 
                         model=gen_config.get("model", "wan-2.2"),
                         mode="api"
                     )
                     self.log_progress(f"Wan 2.2 Video Generation Enabled (Model: {self.wan_client.model})")
                 else:
                     self.log_progress("Wan 2.2 Enabled but API Key missing.", level="warning")

    def execute(self, state: AgentState) -> AgentState:
        if not self.validate_input(state, ["scene_plan"]):
            return state

        # Determine isolation directory
        run_id = getattr(state, 'run_id', 'default')
        run_dir = self.asset_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_progress(f"Fetching visual assets (Run ID: {run_id})")
        
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
                        # Pass run_dir to isolate files
                        result_path, backup = self._fetch_real_image(target_url, idx, run_dir)
                        
                        if result_path:
                             image_path = result_path
                             source = "real_news"
                        elif backup:
                             # Main failed (too small), but backup exists
                             backup_real_path = backup
                             self.log_progress(f"Scene {idx+1}: Real image small. Saved as backup.", level="info")
                    except Exception as e:
                        self.log_progress(f"Real image failed: {e}", level="warning")
                
                # STRATEGY 2a: AI Video Generation (Wan 2.2)
                # Attempt only if enabled and no real image found (or even if found? user preference. Let's prioritize video if scene warrants it)
                # For now, if REAL_FOOTAGE found, we used it. If not, we try Video Gen.
                if not image_path and self.wan_client:
                    query = scene.get("visual", {}).get("image_query", "")
                    if not query:
                        query = f"News footage of {scene.get('location', 'event')}"
                    
                    try:
                        self.log_progress(f"Scene {idx+1}: Generating Video with Wan 2.2...")
                        video_path = self._fetch_wan_video(query, run_dir, idx)
                        if video_path:
                            image_path = video_path
                            source = "generated_wan_video"
                    except Exception as e:
                        self.log_progress(f"Scene {idx+1}: Video generation failed: {e}", level="warning")

                # STRATEGY 2b: AI Image Generation (Fallback) - REMOVED
                # We strictly want Video Generation.
                if not image_path:
                    # If we have real images, maybe fallback to one of them?
                    # The user asked to remove "pollinations and other fallback mechanism"
                    # But keeping "Emergency Real Image" might be acceptable?
                    # "remove the system... that was of generating images from poliination and other fallback mechanism"
                    # This implies strictly NO AI IMAGES.
                    # Real images from news are okay if available.
                    
                    if real_images:
                         self.log_progress(f"Scene {idx+1}: Video failed. Using real news image as fallback.", level="warning")
                         try:
                             # Pick a deterministic random image based on scene index
                             fallback_url = real_images[idx % len(real_images)]
                             res, backup = self._fetch_real_image(fallback_url, idx, run_dir)
                             if res:
                                 image_path = res
                                 source = "real_news_fallback"
                         except Exception as e:
                             self.log_progress(f"Real fallback failed: {e}", level="error")

                if not image_path:
                    raise RuntimeError("Wan 2.2 Video Generation failed and no real news images available.")

                # STRATEGY 5: Text Fallback (Last Resort)
                if not image_path:
                    raise RuntimeError("All visual strategies failed.")

                scene["visual_assets"] = {
                    "image_path": str(image_path),
                    "source": source
                }
            except Exception as e:
                # Dynamic Fallback: Generate a text slide
                fallback_path = self._generate_dynamic_fallback(scene, idx, run_dir)
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

    def _generate_dynamic_fallback(self, scene: Dict[str, Any], idx: int, run_dir: Path) -> Path:
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
        output_path = run_dir / f"fallback_{idx}.jpg"
        img.save(output_path)
        return output_path

    # Composite Upscaling Removed


    # --------------------------------------------------------

    def _fetch_real_image(self, url: str, idx: int, run_dir: Path) -> Path:
        """Download a real image from a URL."""
        import hashlib
        key = hashlib.md5(url.encode()).hexdigest()
        image_path = run_dir / f"real_{key}.jpg"
        
        if image_path.exists():
            return image_path
            
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
             with open(image_path, "wb") as f:
                f.write(response.content)
             
             # Validate Image Size
             # Validate Image Size
             is_small = False
             try:
                 from PIL import Image
                 with Image.open(image_path) as img:
                     width, height = img.size
                     if width < 800 or height < 600:
                         is_small = True
                 
                 if is_small:
                     # DO NOT DELETE. Rename to backup.
                     backup_path = run_dir / f"backup_real_{key}.jpg"
                     if image_path.exists():
                         # Windows Fix: Ensure file is closed before rename
                         try:
                            image_path.replace(backup_path)
                         except OSError:
                            # If still locked, wait briefly or just log (fail safe)
                            import time
                            time.sleep(0.1)
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

    # Pollinations Logic Removed


    def _fetch_wan_video(self, query: str, run_dir: Path, idx: int) -> Path:
        """Generate a video using WanClient."""
        import hashlib
        key = hashlib.md5(query.encode()).hexdigest()
        video_path = run_dir / f"wan_gen_{key}.mp4"
        
        if video_path.exists():
            return video_path
            
        # Use WanClient
        # Optimize prompt for video
        safe_query = query[:400] + ", cinematic, 4k, slow motion, detailed"
        
        video_url = self.wan_client.generate_video(safe_query)
        
        if video_url:
            # Download video
            response = requests.get(video_url, timeout=60)
            if response.status_code == 200:
                with open(video_path, "wb") as f:
                    f.write(response.content)
                return video_path
            else:
                self.log_progress(f"Failed to download generated video: {response.status_code}", level="warning")
        
        return None

    def _resolve_scene_image(self, scene: Dict[str, Any]) -> Path:
        # Legacy method kept for interface compatibility if needed, but logic moved to execute
        pass
