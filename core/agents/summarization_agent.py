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
        self.summary_length = self.content_config.get('summary_length', 250)
    
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
        Also computes date distribution so the LLM can detect outliers.
        """
        from collections import Counter
        formatted_lines = []
        
        # Sort just in case (though should be sorted by collection agent)
        # Handle cases where published_dt might be missing (fallback to string sort)
        try:
             articles.sort(key=lambda x: x.get('published_dt') or x.get('published', ''))
        except:
             pass

        date_tally: Counter = Counter()
        for article in articles:
            # Extract date string YYYY-MM-DD
            date_str = "Unknown Date"
            if article.get('published_dt'):
                date_str = article['published_dt'].strftime("%Y-%m-%d")
            elif article.get('published'):
                date_str = article['published'][:10]

            date_tally[date_str] += 1
            line = f"[{date_str}]\n- {article['title']} ({article.get('source', 'Unknown')})"
            formatted_lines.append(line)

        # Build a date-distribution note for the LLM
        total = len(articles)
        distribution_note = "DATE DISTRIBUTION ACROSS SOURCES:\n" + "\n".join(
            f"  {date}: {count} article(s) ({round(count/total*100)}%)"
            for date, count in date_tally.most_common()
        )

        headlines_block = "\n\n".join(formatted_lines)
        return f"{distribution_note}\n\nHEADLINES:\n{headlines_block}"
    
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
Write a DETAILED NEWS REPORT covering this topic.
Target Length: Approximately {self.summary_length} words.

RULES:
1. **COMPREHENSIVE**: Do not just summarize. Detail the events, background, and implications.
2. **Review the facts**: Ensure that all numbers, dates, and names are accurate.
3. **STRUCTURE**:
   - **Headline**: A strong, engaging headline.
   - **The Lead**: What happened? (Who, when, where).
   - **The Detail**: Context, history (e.g. previous crashes), and eyewitness accounts.
   - **The Outcome**: Investigation status and reactions.
4. **TONE**: Professional, Investigative, Standard Journalism.
5. **No Fluff**: Every sentence must contain information.
6. **DATE ACCURACY — CRITICAL**:
   - RSS feed timestamps can be wrong by ±1 day due to timezone differences (e.g. an event at 11 PM IST appears as the previous day in UTC).
   - Use the DATE DISTRIBUTION provided above to identify the CANONICAL EVENT DATE — the date cited by the clear majority of sources.
   - If a small number of headlines carry a date that is 1 day earlier than the majority, treat those as timezone artifacts; DO NOT use that earlier date as the event date in your report.
   - Always state the event date using the majority-agreed date. Never derive the event date solely from the earliest or first article.

CRITICAL: The report must be substantive and match the target length.

{text}

FINAL NEWS SUMMARY:"""

        # Get specific model for summarization if configured
        model_override = self.config.get('llm', {}).get('agents', {}).get('summarization')
        
        summary = self.llm_client.generate(prompt, model=model_override)
        return summary.strip()
