"""
Scene Planner Agent
Breaks narration into structured storyboard scenes
"""

import json
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentState
from utils.llm_client import LLMClient


class ScenePlannerAgent(BaseAgent):
    """Plans storyboard scenes from narration"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_client = LLMClient(config.get("llm", {}))
        self.scene_config = config.get("scenes", {})
        self.min_duration = self.scene_config.get("min_scene_duration", 8)
        self.max_duration = self.scene_config.get("max_scene_duration", 20)

    def execute(self, state: AgentState) -> AgentState:
        if not self.validate_input(state, ["narration"]):
            return state

        self.log_progress("Planning storyboard scenes")

        try:
            scenes = self._generate_scene_plan(state.narration)
        except Exception as e:
            self.log_progress(f"Scene planning failed, using fallback: {e}", level="warning")
            scenes = self._fallback_scenes(state.narration)

        state.scene_plan = scenes
        self.log_progress(f"Created storyboard with {len(scenes)} scenes")
        return state

    # ------------------------------------------------------------------
    # Core LLM logic
    # ------------------------------------------------------------------

    def _generate_scene_plan(self, narration: str) -> List[Dict[str, Any]]:
        prompt = f"""
You are a professional news video storyboard planner.

Convert the narration into visually meaningful scenes.

RULES:
- Output ONLY valid JSON
- No markdown, no explanation text
- Each scene must be visually concrete
- Durations: {self.min_duration}–{self.max_duration} seconds

JSON FORMAT:
{{
  "scenes": [
    {{
      "scene_id": 1,
      "duration": 12,
      "narration_text": "...",
      "on_screen_text": "...",
      "scene_purpose": "headline | incident | investigation | public_reaction | conclusion",
      "visual_focus": "what should be shown visually",
      "location": "place if relevant",
      "entities": ["people", "objects"],
      "emotion": "neutral | tense | alarming"
    }}
  ]
}}

NARRATION:
{narration}
"""

        response = self.llm_client.generate(prompt)
        data = self.safe_json_load(response)

        scenes = data.get("scenes", [])
        if not scenes:
            raise ValueError("Empty scenes returned by LLM")

        return scenes

    # ------------------------------------------------------------------
    # Safe JSON extraction
    # ------------------------------------------------------------------

    def safe_json_load(self, response: str) -> Dict[str, Any]:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == -1:
                raise ValueError("No JSON found in response")
            return json.loads(response[start:end])
        except Exception as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")

    # ------------------------------------------------------------------
    # Fallback (NEVER REMOVE)
    # ------------------------------------------------------------------

    def _fallback_scenes(self, narration: str) -> List[Dict[str, Any]]:
        sentences = [s.strip() for s in narration.split(".") if s.strip()]
        scenes = []

        for i, text in enumerate(sentences):
            scenes.append({
                "scene_id": i + 1,
                "duration": 12,
                "narration_text": text,
                "on_screen_text": text[:80],
                "scene_purpose": "content",
                "visual_focus": "generic news background",
                "location": None,
                "entities": [],
                "emotion": "neutral"
            })

        return scenes
