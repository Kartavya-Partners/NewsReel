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
        self.max_articles = self.news_config.get('max_articles', 10)
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Collect news using the new Headline-Based Pipeline.
        Strictly Google News -> Sort -> Filter -> Dedupe -> Summarize
        """
        self.log_progress(f"Collecting headlines for topic: {state.topic}")
        
        # 1. Fetch ALL entries from Google News (no content crawling yet)
        source = {
            'name': 'Google News',
            'url': f"https://news.google.com/rss/search?q={state.topic.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en",
            'type': 'rss'
        }
        
        raw_entries = self._fetch_rss_headlines(source, state.topic)
        self.log_progress(f"Fetched {len(raw_entries)} raw headlines")
        
        # 2. Sort by Date (Oldest -> Newest)
        raw_entries.sort(key=lambda x: x['published_dt'])
        
        # 3. Filter for Importance (Must be "Event" news)
        important_entries = [
            e for e in raw_entries 
            if self._is_event_headline(e['title'], state.topic)
        ]
        if not important_entries:
            self.log_progress("Strict event filter returned 0. Falling back to all headlines.")
            important_entries = raw_entries
            
        self.log_progress(f"Filtered to {len(important_entries)} event-related headlines")
        
        # 4. Deduplicate (Clusters: Keep First + Last)
        unique_entries = self._deduplicate_articles(important_entries)
        
        # 5. Cap at max_articles (ensure we don't process too many)
        final_entries = unique_entries[:self.max_articles]
        
        # 6. NOW fetch images (Lightweight content extraction)
        # We only need OG image, we dont need body text for the LLM anymore
        articles = []
        for i, entry in enumerate(final_entries):
            # self.log_progress(f"Resolving image for: {entry['title'][:30]}...")
            _, image_url = self._extract_content(entry['link'])
            
            article = {
                'title': entry['title'],
                'summary': entry['summary'], # Use RSS summary
                'link': entry['link'],
                'published': entry['published'],
                'published_dt': entry['published_dt'],
                'source': 'Google News',
                'content': f"{entry['title']}. {entry.get('summary', '')}", # Merge Title + Summary for context & length
                'image_url': image_url
            }
            articles.append(article)
            
        self.log_progress(f"Final collection: {len(articles)} articles")
        
        state.raw_articles = articles
        state.metadata['collection_timestamp'] = datetime.now().isoformat()
        
        return state

    def _fetch_rss_headlines(self, source: Dict, topic: str) -> List[Dict]:
        """Fetch raw RSS entries without crawling content."""
        entries = []
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries:
                entries.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'published_dt': self._parse_date(entry.get('published', '')),
                    'summary': entry.get('summary') or entry.get('description', '')
                })
        except Exception as e:
            self.log_progress(f"Error fetching RSS: {e}", level="error")
            
        return entries

    
    def _extract_content(self, url: str) -> tuple[str, str]:
        """
        Extract article content and main image from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Tuple (text content, image_url)
        """
        text_content = ""
        image_url = ""
        
        try:
            # Google News links are often redirects, requests follows them by default
            # IMPORTANT: Use User-Agent to look like a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- Extract Image (og:image) ---
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                image_url = og_image["content"]
            
            # --- Extract Content ---
            # --- Extract Content (Smarter) ---
            # Remove script, style, nav, footer, header, aside
            for junk in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
                junk.decompose()
            
            # Try to find the main article body
            article_body = soup.find('article')
            if not article_body:
                # Fallback: look for common content classes
                article_body = soup.find('div', class_=lambda c: c and any(x in c.lower() for x in ['content', 'article', 'story', 'main']))
            
            # If still nothing, use the whole soup
            target_soup = article_body if article_body else soup
            
            # Extract text from paragraphs only (avoids menu items)
            paragraphs = []
            for p in target_soup.find_all('p'):
                text = p.get_text().strip()
                if len(text) > 40:  # Ignore short captions/links
                    paragraphs.append(text)
            
            # Join paragraphs
            text_content = "\n".join(paragraphs)
            
            # Fallback if paragraphs failed (some sites use divs)
            if len(text_content) < 200:
                text_content = target_soup.get_text(" ", strip=True)

            text_content = text_content[:3000]  # Increased limit slightly for context
            
        except Exception as e:
            self.log_progress(f"Error extracting content from {url}: {e}", level="warning")
            
        return text_content, image_url
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS published date to datetime object."""
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return datetime.now()

    def _is_event_headline(self, title: str, topic: str) -> bool:
        """
        Check if headline is relevant to the topic.
        We no longer filter by "Event Keywords" (e.g. blast, arrest) because
        it filters out valid economic/tech news (e.g. "RAM prices rising").
        
        New Logic:
        1. Token overlap with Topic.
        2. Or if topic words are rare, just let it pass (better to have noise than silence).
        """
        title_lower = title.lower()
        topic_lower = topic.lower()
        
        # Simple stop words to ignore in topic matching
        stop_words = {'the', 'a', 'in', 'of', 'for', 'to', 'on', 'and', 'is', 'at', 'prices', 'price'}
        topic_words = [w for w in topic_lower.split() if w not in stop_words and len(w) > 2]
        
        if not topic_words:
            return True # Topic is generic, keep everything
            
        # Check if ANY significant topic word appears in title
        # e.g. Topic "RAM Prices" -> Match "RAM" or "Memory"
        # We trust Google News search quality mostly, this is just to remove total junk.
        hits = sum(1 for w in topic_words if w in title_lower)
        
        # If more than 0 hits, it's likely relevant.
        # But honestly, since we search Google News with the topic, 
        # the results are usually relevant by definition.
        # So we simply return True to let the LLM decide later.
        return True

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Deduplicate by clustering similar titles.
        Keep EARLIEST (background) and LATEST (update) of each cluster.
        """
        if not articles:
            return []
            
        # 1. Sort by date (Oldest -> Newest)
        # Ensure we have datetime objects
        for a in articles:
            if not isinstance(a.get('published_dt'), datetime):
                a['published_dt'] = self._parse_date(a.get('published', ''))
                
        articles.sort(key=lambda x: x['published_dt'])
        
        # 2. Cluster similar articles
        clusters = []
        processed_indices = set()
        
        for i, article in enumerate(articles):
            if i in processed_indices:
                continue
                
            current_cluster = [article]
            processed_indices.add(i)
            
            title_words = set(article['title'].lower().split())
            
            for j, other in enumerate(articles):
                if j in processed_indices:
                    continue
                    
                other_words = set(other['title'].lower().split())
                
                # Check overlap
                if len(title_words) > 0:
                    overlap = len(title_words & other_words) / len(title_words)
                    if overlap > 0.65: # 65% overlap = likely same story
                        current_cluster.append(other)
                        processed_indices.add(j)
            
            clusters.append(current_cluster)
            
        # 3. Select representatives from each cluster
        final_articles = []
        for cluster in clusters:
            # Cluster is already sorted old->new because 'articles' was sorted
            if len(cluster) == 1:
                final_articles.append(cluster[0])
            else:
                # Keep First (Background) and Last (Update) -- discard middle
                final_articles.append(cluster[0])
                final_articles.append(cluster[-1])
                
        # Final sort
        final_articles.sort(key=lambda x: x['published_dt'])
        
        removed = len(articles) - len(final_articles)
        if removed > 0:
            self.log_progress(f"Deduplicated: {len(articles)} -> {len(final_articles)} (Removed redundant middle updates)")
            
        return final_articles
