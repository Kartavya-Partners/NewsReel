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
        prompt = f"""Write a natural spoken narration script for a short video based on this summary.
Target length: {target_words} words.

IMPORTANT INSTRUCTIONS:
1. Write ONLY the spoken words. 
2. Do NOT include speaker labels like 'News Anchor:', 'Narrator:', or 'Host:'.
3. Do NOT include stage directions or visual descriptions in brackets.
4. Do NOT verify or spell out punctuation (e.g., do NOT write 'dot', 'comma').
5. INCLUDE SPECIFIC FACTS from the summary: Date, Time, Location, Death Toll (if mentioned).
6. Start with a strong lead sentence mentioning the location and event.
7. Make it sound professional yet engaging, like a TV news segment.

Topic: {topic}
Summary: {summary}

Narration Script:"""

        narration = self.llm_client.generate(prompt)
        return self._clean_narration(narration)

    def _clean_narration(self, text: str) -> str:
        """Remove metadata, notes, and stage directions."""
        import re
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip metadata lines like "Title:", "Note:", "Narration Script:"
            # Also catch conversational fillers like "Here's the narration script:"
            if re.match(r'^(Title|Note|Topic|Summary|Narration|Script|Here is|Here\'s|Audio)(:| )', line, re.IGNORECASE):
                continue
            
            # Remove "News Anchor:" prefixes
            line = re.sub(r'^\s*(News Anchor|Host|Narrator|Presenter)(\s*:)?\s*', '', line, flags=re.IGNORECASE)
            
            # Remove quotes if the entire line is quoted
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            
            # Remove content in brackets/parentheses if it looks like direction
            line = re.sub(r'\[.*?\]', '', line)
            line = re.sub(r'\(.*?\)', '', line)

            if line.strip():
                cleaned_lines.append(line.strip())
                
        # Join and one last cleanup of conversational prefixes in the full text
        full_text = " ".join(cleaned_lines)
        full_text = re.sub(r"^(Here's|Here is) the (narration|script).*?(:|\.)", "", full_text, flags=re.IGNORECASE).strip()
        
        return full_text
