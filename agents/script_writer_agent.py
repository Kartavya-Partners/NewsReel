"""Script Writer Agent - Converts summaries to natural narration."""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentState
from utils.llm_client import LLMClient


class ScriptWriterAgent(BaseAgent):
    """Agent responsible for writing natural narration scripts."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_client = LLMClient(config.get('llm', {}))
        self.content_config = config.get('content', {})
        self.narration_style = self.content_config.get('narration_style', 'neutral')
        self.target_duration = self.content_config.get('target_duration', 90)
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Convert summary into natural spoken narration.
        
        Args:
            state: Current agent state with summary
            
        Returns:
            Updated state with narration
        """
        if not self.validate_input(state, ['summary']):
            return state
        
        self.log_progress("Writing narration script")
        
        narration = self._generate_narration(state.summary, state.topic)
        
        state.narration = narration
        self.log_progress(f"Generated narration ({len(narration.split())} words)")
        
        return state
    
    def _generate_narration(self, summary: str, topic: str) -> str:
        """
        Generate natural narration from summary.
        
        Args:
            summary: Factual summary
            topic: Topic of the news
            
        Returns:
            Natural narration script
        """
        # Calculate approximate word count for target duration
        # Average speaking rate: 150 words per minute
        target_words = int((self.target_duration / 60) * 150)
        
        # Simplified prompt
        prompt = f"""Convert this summary into a natural spoken script for a video ({target_words} words).

Topic: {topic}
Summary: {summary}

Script:"""

        narration = self.llm_client.generate(prompt)
        return narration.strip()
