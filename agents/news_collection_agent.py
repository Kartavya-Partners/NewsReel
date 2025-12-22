"""News Collection Agent - Fetches news from various sources."""

import feedparser
import requests
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from .base_agent import BaseAgent, AgentState


class NewsCollectionAgent(BaseAgent):
    """Agent responsible for collecting news from RSS feeds and APIs."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.news_config = config.get('news', {})
        self.sources = self.news_config.get('sources', [])
        self.max_articles = self.news_config.get('max_articles', 5)
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Fetch news articles based on topic and category.
        
        Args:
            state: Current agent state with topic
            
        Returns:
            Updated state with raw_articles
        """
        self.log_progress(f"Collecting news for topic: {state.topic}")
        
        articles = []
        
        # Fetch from RSS feeds
        for source in self.sources:
            if source['type'] == 'rss':
                articles.extend(self._fetch_rss(source, state.topic))
        
        # Deduplicate articles
        articles = self._deduplicate_articles(articles)
        
        # Limit to max_articles
        articles = articles[:self.max_articles]
        
        self.log_progress(f"Collected {len(articles)} articles")
        
        state.raw_articles = articles
        state.metadata['collection_timestamp'] = datetime.now().isoformat()
        
        return state
    
    def _fetch_rss(self, source: Dict, topic: str) -> List[Dict]:
        articles = []

        try:
            self.log_progress(f"Fetching from {source['name']}")

            if source['name'].lower() == "google news":
                url = f"https://news.google.com/rss/search?q={topic.replace(' ', '+')}"
            else:
                url = source['url']

            feed = feedparser.parse(url)

            self.log_progress(f"RSS entries found: {len(feed.entries)}")


            for entry in feed.entries:
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary') or entry.get('description', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': source['name'],
                    'content': self._extract_content(entry.get('link', ''))
                }
                articles.append(article)

            self.log_progress(f"Collected {len(articles)} articles from {source['name']}")

        except Exception as e:
            self.log_progress(f"Error fetching from {source['name']}: {e}", level="error")

        return articles

    
    def _extract_content(self, url: str) -> str:
        """
        Extract article content from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted text content
        """
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:2000]  # Limit content length
            
        except Exception as e:
            self.log_progress(f"Error extracting content from {url}: {e}", level="warning")
            return ""
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Remove duplicate articles based on title similarity.
        
        Args:
            articles: List of articles
            
        Returns:
            Deduplicated list
        """
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title_lower = article['title'].lower()
            
            # Simple deduplication - check if similar title exists
            is_duplicate = False
            for seen_title in seen_titles:
                # If 80% of words match, consider duplicate
                title_words = set(title_lower.split())
                seen_words = set(seen_title.split())
                
                if len(title_words) > 0:
                    overlap = len(title_words & seen_words) / len(title_words)
                    if overlap > 0.8:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                seen_titles.add(title_lower)
                unique_articles.append(article)
        
        removed = len(articles) - len(unique_articles)
        if removed > 0:
            self.log_progress(f"Removed {removed} duplicate articles")
        
        return unique_articles
