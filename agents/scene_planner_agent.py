"""Scene Planner Agent - Breaks narration into visual scenes."""

import json
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentState
from utils.llm_client import LLMClient


class ScenePlannerAgent(BaseAgent):
    """Agent responsible for planning visual scenes."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_client = LLMClient(config.get('llm', {}))
        self.scene_config = config.get('scenes', {})
        self.min_duration = self.scene_config.get('min_scene_duration', 8)
        self.max_duration = self.scene_config.get('max_scene_duration', 20)
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Break narration into visual scenes with animation suggestions.
        
        Args:
            state: Current agent state with narration
            
        Returns:
            Updated state with scene_plan
        """
        if not self.validate_input(state, ['narration']):
            return state
        
        self.log_progress("Planning visual scenes")
        
        scene_plan = self._generate_scene_plan(state.narration)
        
        state.scene_plan = scene_plan
        self.log_progress(f"Created plan with {len(scene_plan)} scenes")
        
        return state
    
    def _generate_scene_plan(self, narration: str) -> List[Dict]:
        """
        Generate scene plan from narration.
        
        Args:
            narration: Narration script
            
        Returns:
            List of scene dictionaries
        """
        prompt = f"""You are an expert video scene planner for animated explainer videos.

Break the following narration into logical visual scenes suitable for animation.

Requirements:
- Each scene should be {self.min_duration}-{self.max_duration} seconds
- Provide clear visual suggestions for each scene
- Suggest appropriate animations (text, icons, graphs, transitions)
- Ensure smooth flow between scenes

Output MUST be valid JSON in this exact format:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "duration": 12,
      "narration_text": "exact text from narration for this scene",
      "on_screen_text": "key text to display",
      "visual_type": "headline|content|data|conclusion",
      "animation_suggestion": "detailed description of animation"
    }}
  ]
}}

Narration:
{narration}

Scene Plan (JSON):"""

        response = self.llm_client.generate(prompt)
        
        try:
            # Parse JSON response
            scene_data = json.loads(response)
            scenes = scene_data.get('scenes', [])
            
            # Validate and clean scenes
            validated_scenes = []
            for scene in scenes:
                if all(k in scene for k in ['scene_number', 'duration', 'narration_text']):
                    validated_scenes.append(scene)
            
            return validated_scenes
            
        except json.JSONDecodeError as e:
            self.log_progress(f"Error parsing scene plan JSON: {e}", level="error")
            # Fallback: create simple scene plan
            return self._create_fallback_scenes(narration)
    
    def _create_fallback_scenes(self, narration: str) -> List[Dict]:
        """
        Create simple fallback scene plan if LLM fails.
        
        Args:
            narration: Narration script
            
        Returns:
            Basic scene plan
        """
        # Split narration into sentences
        sentences = [s.strip() + '.' for s in narration.split('.') if s.strip()]
        
        scenes = []
        scene_num = 1
        
        for i in range(0, len(sentences), 2):
            text = ' '.join(sentences[i:i+2])
            
            scene = {
                'scene_number': scene_num,
                'duration': 15,
                'narration_text': text,
                'on_screen_text': text[:50] + '...' if len(text) > 50 else text,
                'visual_type': 'content',
                'animation_suggestion': 'Animated text with fade in/out'
            }
            
            scenes.append(scene)
            scene_num += 1
        
        self.log_progress("Using fallback scene plan", level="warning")
        return scenes
