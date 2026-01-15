"""
Visual Planner Agent
Enhances scenes with concrete visual instructions
"""

import json
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentState
from core.utils.llm_client import LLMClient


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
            self.log_progress(f"Batch processing failed: {e}. Reverting to rule-based fallback.", level="error")
            # Fallback to pure rule-based (NO LLM) to save quota
            enhanced_scenes = []
            for scene in state.scene_plan:
                enhanced_scenes.append(self._fallback_visual(scene))

        state.scene_plan = enhanced_scenes
        self.log_progress("Visual planning completed")
        return state

    def _enhance_scenes_batch(self, scenes: List[Dict]) -> List[Dict]:
        """Process ALL scenes in ONE single LLM call to save quota."""
        self.log_progress(f"Enhancing {len(scenes)} scenes in ONE batch...")
        
        # Prepare mini representation
        mini_scenes = []
        for s in scenes:
            mini_scenes.append({
                "id": s.get("scene_id"),
                "text": s.get("narration_text", "")[:150], 
                "visual_note": s.get("visual", {}).get("visual_focus", "")
            })
            
        prompt = f"""
        You are a visual director for news explainer videos.
        
        INPUT SCRIPT:
        {json.dumps(mini_scenes, indent=2)}

        TASK:
        Generate a JSON list of logical visual plans for ALL these scenes.

        CRITICAL INSTRUCTIONS:
        1. Classify scene type: 'RE_ENACTMENT' (action), 'REAL_FOOTAGE' (places), 'INFOGRAPHIC' (concepts).
        2. Assign 'camera_motion': 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'.
        3. 'lower_third_text': Short headline (MAX 6 WORDS). OMIT if no specific info.
        4. 'image_query': Detailed prompt. rules:
           - FORCE 'Location/Country' context (e.g., "New Delhi India").
           - NO TEXT/CHARTS: Do NOT ask for "charts", "graphs", or "signs".
           - STYLE: "Cinematic, Unreal Engine 5, Photorealistic, No Text".
           - IMPORTANT: If the scene describes a specific event, use 'RE_ENACTMENT' and describe the action vividly.

        OUTPUT FORMAT (Strict JSON List):
        [
            {{
                "id": 1, 
                "visual": {{ ... }}
            }}
        ]
        """
        
        try:
            response = self.llm_client.generate(prompt)
            
            # Parse List
            try:
                start = response.find("[")
                end = response.rfind("]") + 1
                if start == -1 or end == 0: raise ValueError("No list found")
                json_str = response[start:end]
                plans = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                import re
                # Clean up and try again
                json_str = re.sub(r'```json', '', response)
                json_str = json_str.replace('```', '')
                start = json_str.find("[")
                end = json_str.rfind("]") + 1
                if start != -1:
                    plans = json.loads(json_str[start:end])
                else:
                    raise
            
            # Merge Results
            enhanced_scenes = []
            for scene in scenes:
                # Find matching plan by ID
                plan = next((p for p in plans if p.get("id") == scene.get("scene_id")), None)
                
                if plan and "visual" in plan:
                    # Update visual
                    scene["visual"] = plan["visual"]
                else:
                    # Use Rule-Based Fallback (No Cost)
                    scene["visual"] = self._fallback_visual(scene)["visual"]
                
                enhanced_scenes.append(scene)
                
            return enhanced_scenes

        except Exception as e:
            self.log_progress(f"Batch visualization failed: {e}. Using rule-based fallback.", level="error")
            # Fallback for ALL without calling LLM again
            fallback_scenes = []
            for s in scenes:
                fallback_scenes.append(self._fallback_visual(s))
            return fallback_scenes

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
