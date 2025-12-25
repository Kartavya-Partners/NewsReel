"""
Visual Planner Agent
Enhances scenes with concrete visual instructions
"""

import json
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentState
from utils.llm_client import LLMClient


class VisualPlannerAgent(BaseAgent):
    """Adds visual intelligence to storyboard scenes"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_client = LLMClient(config.get("llm", {}))

    def execute(self, state: AgentState) -> AgentState:
        if not self.validate_input(state, ["scene_plan"]):
            return state

        self.log_progress("Enhancing scenes with visual planning (BATCH MODE)")

        try:
            # Attempt Batch Processing for Speed (17m -> 2m)
            enhanced_scenes = self._enhance_scenes_batch(state.scene_plan)
        except Exception as e:
            self.log_progress(f"Batch processing failed: {e}. Reverting to sequential.", level="error")
            # Fallback to sequential
            enhanced_scenes = []
            for scene in state.scene_plan:
                try:
                    enhanced_scenes.append(self._enhance_scene(scene))
                except Exception as seq_e:
                    enhanced_scenes.append(self._fallback_visual(scene))

        state.scene_plan = enhanced_scenes
        self.log_progress("Visual planning completed")
        return state

    def _enhance_scenes_batch(self, scenes: List[Dict]) -> List[Dict]:
        """Process scenes in chunks to avoid LLM timeouts/Hallucinations."""
        chunk_size = 4  # Process 4 scenes at a time (Safe for local LLM)
        enhanced_all = []
        
        # Helper for chunking
        for i in range(0, len(scenes), chunk_size):
            chunk = scenes[i : i + chunk_size]
            self.log_progress(f"Processing batch chunk {i//chunk_size + 1} (Scenes {i+1}-{min(i+chunk_size, len(scenes))})")
            
            try:
                # Process this chunk
                processed_chunk = self._process_chunk(chunk, start_id=i)
                enhanced_all.extend(processed_chunk)
            except Exception as e:
                self.log_progress(f"Chunk failed: {e}. Using fallback for this chunk.", level="warning")
                for s in chunk:
                    enhanced_all.append(self._fallback_visual(s))
                    
        return enhanced_all

    def _process_chunk(self, chunk_scenes: List[Dict], start_id: int) -> List[Dict]:
        """Process a small specific list of scenes."""
        mini_scenes = []
        for j, s in enumerate(chunk_scenes):
            mini_scenes.append({
                "id": start_id + j,
                "text": s.get("narration_text", "")[:200], # Limit text length
                "visual_note": s.get("visual_description", "")
            })
            
        prompt = f"""
        You are a visual director for news explainer videos.
        
        INPUT SCRIPT CHUNK:
        {json.dumps(mini_scenes, indent=2)}

        TASK:
        Generate a JSON list of logical visual plans for these {len(chunk_scenes)} scenes.

        CRITICAL INSTRUCTIONS:
        1. Classify scene type: 'RE_ENACTMENT', 'REAL_FOOTAGE', 'INFOGRAPHIC'.
        2. Assign 'camera_motion': 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'.
        3. 'lower_third_text': Short headline. OMIT if no specific info.
        4. 'image_query': Detailed prompt for AI image (Unreal Engine 5 style).

        OUTPUT FORMAT (Strict JSON List):
        [
            {{
                "id": {start_id}, 
                "visual": {{ ... }}
            }}
        ]
        """
        
        response = self.llm_client.generate(prompt)
        
        # Parse
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start == -1 or end == 0: raise ValueError("No list found")
            json_str = response[start:end]
            plans = json.loads(json_str)
        except json.JSONDecodeError:
            import re
            fixed = re.sub(r',\s*\]', ']', json_str)
            plans = json.loads(fixed)
            
        # Merge
        result_chunk = []
        for x, scene in enumerate(chunk_scenes):
            scene_id = start_id + x
            plan = next((p for p in plans if p.get("id") == scene_id), None)
            
            if plan and "visual" in plan:
                scene["visual"] = plan["visual"]
            else:
                scene["visual"] = self._fallback_visual(scene)["visual"]
            result_chunk.append(scene)
            
        return result_chunk

    # ------------------------------------------------------------------
    # Core LLM logic
    # ------------------------------------------------------------------

    def _enhance_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a visual director for news explainer videos.

        Enhance the following scene with VISUAL instructions.
        
        INPUT SCENE:
        {json.dumps(scene, indent=2)}

        CRITICAL INSTRUCTIONS:
        1. Classify scene type: 'REAL_FOOTAGE', 'RE_ENACTMENT', or 'INFOGRAPHIC'.
        2. Construct a 'image_query' optimized for AI Image Generation (Unreal Engine 5 style).
        3. Output ONLY valid JSON.
        
        GUIDANCE:
        - If the scene describes an EVENT (explosion, arrest, raid):
            - Scene Type: 'RE_ENACTMENT'
            - Motion: 'zoom_in' (Breaking news feel)
            - Query: "Hyper-realistic 3D render of [ACTION], dramatic lighting, isometric view, unreal engine 5, news broadcast style"
        - If specific PLACE/PERSON is named:
            - Scene Type: 'REAL_FOOTAGE'
            - Motion: 'pan_right' (Investigation feel) or 'zoom_out' (Reveal)
        - If abstract:
            - Scene Type: 'INFOGRAPHIC'
            - Motion: 'pan_left' or 'zoom_in' (slow)

        OUTPUT FORMAT:
        {{
            "visual": {{
                "scene_type": "RE_ENACTMENT",
                "image_query": "Hyper-realistic 3D render of car explosion at Red Fort, isometric view, dramatic lighting, police tape, news broadcast style",
                "visual_style": "3d_render",
                "camera_motion": "zoom_in", 
                "lower_third_text": "Short headline. Extract specific Date/Location ONLY if present in source text. If missing, omit them. DO NOT INVENT.",
                "overlay_elements": ["breaking_news_banner"]
            }}
        }}
"""

        response = self.llm_client.generate(prompt)
        data = self.safe_json_load(response)

        scene["visual"] = data["visual"]
        return scene

    # ------------------------------------------------------------------
    # Safe JSON extraction
    # ------------------------------------------------------------------

    def safe_json_load(self, response: str) -> Dict[str, Any]:
        import re
        
        # Clean markdown code blocks
        if "```" in response:
            pattern = r"```(?:json)?\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                response = match.group(1)
        
        # Strip confusing prefix/suffix
        response = response.strip()
        
        # Find outer braces
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start == -1 or end == -1:
             raise ValueError("No JSON object found in response")
             
        json_str = response[start:end]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # First retry: Fix trailing commas
            try:
                fixed_str = re.sub(r',\s*([\]}])', r'\1', json_str)
                return json.loads(fixed_str)
            except:
                pass
            
            # Second retry: Regex extraction (The nuclear option)
            # If standard JSON parsing fails, we extract what we can using regex
            # This is robust to missing commas, unescaped quotes, etc.
            self.log_progress("JSON parse failed, attempting regex extraction...", level="warning")
            return self._regex_extract_visual(json_str)

    def _regex_extract_visual(self, text: str) -> Dict[str, Any]:
        """Last resort extraction of visual fields using regex."""
        import re
        
        # Helper to extract a single field
        def extract(key, default):
            # Look for "key": "value" or "key": 'value'
            # We use non-greedy matching .*? and handle escaped quotes poorly but good enough for simple text
            pattern = rf'"{key}"\s*:\s*"(.*?)"'
            match = re.search(pattern, text)
            if match:
                return match.group(1)
            return default

        # Extract list helper
        def extract_list(key):
            pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                # cleaner split
                items = match.group(1).split(',')
                return [i.strip().strip('"').strip("'") for i in items if i.strip()]
            return []

        return {
            "visual": {
                "scene_type": extract("scene_type", "RE_ENACTMENT"),
                "image_query": extract("image_query", "Hyper-realistic 3D render of news event, unreal engine 5"),
                "visual_style": extract("visual_style", "3d_render"),
                "camera_motion": extract("camera_motion", "pan_slow"),
                "lower_third_text": extract("lower_third_text", ""),
                "overlay_elements": extract_list("overlay_elements")
            }
        }

    # ------------------------------------------------------------------
    # Fallback (CRITICAL)
    # ------------------------------------------------------------------

    def _fallback_visual(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        scene["visual"] = {
            "image_query": f"{scene.get('location', '')} news event",
            "visual_style": "photo",
            "camera_motion": "static",
            "lower_third_text": scene.get("on_screen_text", "")[:50],
            "overlay_elements": []
        }
        return scene
