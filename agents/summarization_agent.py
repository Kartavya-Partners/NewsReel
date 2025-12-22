"""Summarization Agent - Creates concise summaries using LLM."""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentState
from utils.llm_client import LLMClient


class SummarizationAgent(BaseAgent):
    """Agent responsible for summarizing news articles."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_client = LLMClient(config.get('llm', {}))
        self.content_config = config.get('content', {})
        self.summary_length = self.content_config.get('summary_length', 150)
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Summarize filtered articles into a concise narrative.
        
        Args:
            state: Current agent state with filtered_articles
            
        Returns:
            Updated state with summary
        """
        if not self.validate_input(state, ['filtered_articles']):
            return state
        
        self.log_progress("Creating summary from articles")
        
        # Combine all article content
        combined_text = self._combine_articles(state.filtered_articles)
        
        # Generate summary using LLM
        summary = self._generate_summary(combined_text, state.topic)
        
        state.summary = summary
        self.log_progress(f"Generated summary ({len(summary.split())} words)")
        
        return state
    
    def _combine_articles(self, articles: list) -> str:
        """
        Combine multiple articles into single text.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Combined text
        """
        combined = []
        
        for article in articles:
            text = f"Title: {article['title']}\n"
            text += f"Content: {article.get('content', article.get('summary', ''))}\n"
            combined.append(text)
        
        return "\n\n".join(combined)
    
    def _generate_summary(self, text: str, topic: str) -> str:
        """
        Generate summary using LLM.
        
        Args:
            text: Combined article text
            topic: Topic of the news
            
        Returns:
            Generated summary
        """
        # Simplified, more direct prompt
        prompt = f"""Summarize these news articles about "{topic}" in {self.summary_length} words.

Articles:
{text[:3000]}

Summary ({self.summary_length} words):"""

        summary = self.llm_client.generate(prompt)
        return summary.strip()
