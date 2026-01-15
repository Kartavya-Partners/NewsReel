"""Summarization Agent - Creates concise summaries using LLM."""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentState
from core.utils.llm_client import LLMClient


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
        
        # Log for UI display
        self.log_progress(f"\n{'='*40}\nGENERATED SUMMARY:\n{summary}\n{'='*40}")
        
        return state
    
    def _combine_articles(self, articles: list) -> str:
        """
        Format articles into a chronological list of headlines.
        """
        formatted_lines = []
        
        # Sort just in case (though should be sorted by collection agent)
        # Handle cases where published_dt might be missing (fallback to string sort)
        try:
             articles.sort(key=lambda x: x.get('published_dt') or x.get('published', ''))
        except:
             pass

        for article in articles:
            # Extract date string YYYY-MM-DD
            date_str = "Unknown Date"
            if article.get('published_dt'):
                date_str = article['published_dt'].strftime("%Y-%m-%d")
            elif article.get('published'):
                date_str = article['published'][:10]
                
            line = f"[{date_str}]\n- {article['title']} ({article.get('source', 'Unknown')})"
            formatted_lines.append(line)
        
        return "\n\n".join(formatted_lines)
    
    def _generate_summary(self, text: str, topic: str) -> str:
        """
        Generate summary using Senior Newsroom Editor prompt.
        """
        # DEBUG: Save input to file
        try:
            with open("debug_summary_input.txt", "w", encoding="utf-8") as f:
                f.write(f"PROMPT INPUT (HEADLINES):\n{text}")
        except:
            pass

        prompt = f"""You are a senior newsroom editor.

Topic: "{topic}"

You are given VERIFIED Google News headlines ordered from OLDEST to LATEST.

TASK:
Write ONE concise news paragraph exactly like a professional news bulletin.

RULES:
1. Follow strict chronological order (previous → latest).
2. Treat early headlines as BACKGROUND and later ones as UPDATES.
3. Mention dates, locations, authorities, and actions clearly.
4. Do NOT invent facts.
5. If headlines refer to different years or unrelated events, clearly state that no single recent incident exists.

STYLE:
- Neutral
- Factual
- Newsroom tone (BBC / Reuters)
- No storytelling, no opinions
- CRITICAL: Ensure the summary ends with a complete sentence describing the current status, future implications, or what is expected next.

HEADLINES:
{text}

FINAL NEWS SUMMARY:"""

        # Get specific model for summarization if configured
        model_override = self.config.get('llm', {}).get('agents', {}).get('summarization')
        
        summary = self.llm_client.generate(prompt, model=model_override)
        return summary.strip()
