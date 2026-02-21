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
        
        # 1. Fetch ALL entries from Google News with DATE FILTER
        # &when=2y ensures we get the latest news (last 2 years) but avoid ancient 2018 history.
        # &ceid=US:en ensures English results.
        source = {
            'name': 'Google News',
            'url': f"https://news.google.com/rss/search?q={state.topic.replace(' ', '+')}+when:2y&hl=en-US&gl=US&ceid=US:en",
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
        
        # 4. Elite Clustering: Group by title similarity and rank by cluster size
        clusters = self._cluster_by_similarity(important_entries)
        # Sort clusters by size (popularity) and take top 6
        top_clusters = sorted(clusters, key=len, reverse=True)[:6]
        
        # 5. Selective Deep Extraction
        articles = []
        extracted_links = set()
        
        for cluster_idx, cluster in enumerate(top_clusters):
            # Try to get high-quality content for this cluster
            self.log_progress(f"Processing Elite Cluster {cluster_idx+1}/{len(top_clusters)} ({len(cluster)} sources)")
            
            cluster_article = None
            # Try up to 2 sources per cluster for efficiency
            for entry in cluster[:2]:
                content, image_url = self._extract_content(entry['link'])
                
                if self._is_high_quality_content(content):
                    cluster_article = {
                        'title': entry['title'],
                        'summary': entry['summary'],
                        'link': entry['link'],
                        'published': entry['published'],
                        'published_dt': entry['published_dt'],
                        'source': entry.get('source', 'Google News'),
                        'content': content,
                        'image_url': image_url,
                        'is_deep': True # Flag for LLM awareness
                    }
                    extracted_links.add(entry['link'])
                    break
            
            if cluster_article:
                articles.append(cluster_article)
            else:
                self.log_progress(f"Cluster {cluster_idx+1}: No high-quality content found. Falling back to RSS summary.", level="warning")
                # Fallback to the first item's RSS summary
                entry = cluster[0]
                articles.append({
                    'title': entry['title'],
                    'summary': entry['summary'],
                    'link': entry['link'],
                    'published': entry['published'],
                    'published_dt': entry['published_dt'],
                    'source': entry.get('source', 'Google News'),
                    'content': f"{entry['title']}. {entry.get('summary', '')}",
                    'image_url': '',
                    'is_deep': False
                })
        
        # 6. Fill remaining slots with unique non-elite headlines for context
        remaining_budget = self.max_articles - len(articles)
        if remaining_budget > 0:
            # Flatten all clusters into a single list of unique entries
            all_unique_entries = [item for cluster in clusters for item in cluster]
            for entry in all_unique_entries:
                if entry['link'] not in extracted_links and len(articles) < self.max_articles:
                    articles.append({
                        'title': entry['title'],
                        'summary': entry['summary'],
                        'link': entry['link'],
                        'published': entry['published'],
                        'published_dt': entry['published_dt'],
                        'source': entry.get('source', 'Google News'),
                        'content': f"{entry['title']}. {entry.get('summary', '')}",
                        'image_url': '',
                        'is_deep': False
                    })

        
        # 8. Update state and log progress
        state.raw_articles = articles
        state.metadata['collection_timestamp'] = datetime.now().isoformat()
        state.metadata['article_counts'] = {
            'raw': len(important_entries),
            'filtered': len(articles),
            'deep': sum(1 for a in articles if a.get('is_deep'))
        }
        
        self.log_progress(f"Final collection: {len(articles)} articles ({state.metadata['article_counts']['deep']} depth-extracted)")

        
        # PERSISTENT LOGGING: Save articles to output/results/articles_fetched.json for user review
        try:
            import json
            from pathlib import Path
            output_dir = Path("output/results")
            output_dir.mkdir(parents=True, exist_ok=True)
            fetched_path = output_dir / "articles_fetched.json"

            
            # Serialize for JSON
            def _ser(a):
                d = dict(a)
                if 'published_dt' in d:
                    d['published_dt'] = d['published_dt'].isoformat()
                return d
                
            with open(fetched_path, "w", encoding="utf-8") as f:
                json.dump({
                    "topic": state.topic,
                    "timestamp": state.metadata['collection_timestamp'],
                    "count": len(articles),
                    "articles": [_ser(a) for a in articles]
                }, f, indent=2, ensure_ascii=False)
            self.log_progress(f"Saved articles to: {fetched_path}")
        except Exception as e:
            self.log_progress(f"Failed to save articles_fetched.json: {e}", level="warning")
        
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

            text_content = text_content[:30000]  # Increased to 30k to capture full live blogs/speeches
            
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

    def _is_high_quality_content(self, text: str) -> bool:
        """
        Check if the extracted text is useful for LLM summarization.
        Filters out short pages, paywalls, and cookie junk.
        """
        if not text or len(text.strip()) < 600:
            return False
            
        text_lower = text.lower()
        
        # Paywall / Junk keywords
        junk_indicators = [
            "subscribe to read",
            "sign in to continue",
            "enable javascript",
            "access to this page has been denied",
            "page not found",
            "cookie policy",
            "this content is available to subscribers"
        ]
        
        for indicator in junk_indicators:
            if indicator in text_lower:
                return False
                
        return True

    def _cluster_by_similarity(self, entries: List[Dict]) -> List[List[Dict]]:
        """Group entries into clusters of similar stories."""
        if not entries:
            return []
            
        clusters = []
        processed_indices = set()
        
        for i, entry in enumerate(entries):
            if i in processed_indices:
                continue
                
            current_cluster = [entry]
            processed_indices.add(i)
            
            title_words = set(entry['title'].lower().split())
            
            for j, other in enumerate(entries):
                if j in processed_indices:
                    continue
                    
                other_words = set(other['title'].lower().split())
                
                # Check overlap (common words vs total words)
                if len(title_words) > 0:
                    overlap = len(title_words & other_words) / len(title_words)
                    if overlap > 0.60: # 60% overlap
                        current_cluster.append(other)
                        processed_indices.add(j)
            
            clusters.append(current_cluster)
            
        return clusters

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

    def _reconcile_dates(self, articles: List[Dict]) -> List[Dict]:
        """
        Fix RSS timezone-drift date artifacts using majority-vote.

        RSS feeds often report dates in UTC, while events happen in local time
        (e.g. IST = UTC+5:30). This can shift an article's published date one
        day earlier than the actual event date shown on the article page.

        Strategy:
          1. Count how many articles fall on each calendar date.
          2. The most frequent date is treated as the CANONICAL event date.
          3. Any article whose date differs from the canonical date by exactly
             1 day is reassigned to the canonical date and a warning is logged.
          4. If the canonical date itself is uncertain (no clear majority or
             difference > 1 day) the article is left untouched.
        """
        if not articles:
            return articles

        from collections import Counter

        # Build a frequency map of dates (as date objects)
        date_counts: Counter = Counter()
        for art in articles:
            dt = art.get('published_dt')
            if dt and hasattr(dt, 'date'):
                date_counts[dt.date()] += 1
            elif dt and hasattr(dt, 'year'):  # already a date
                date_counts[dt] += 1

        if not date_counts:
            return articles  # no parseable dates — nothing to do

        # Majority date = the date cited by the most articles
        canonical_date, canonical_count = date_counts.most_common(1)[0]
        total = len(articles)

        self.log_progress(
            f"Date reconciliation: majority date={canonical_date} "
            f"({canonical_count}/{total} articles)"
        )

        # Only correct if the majority date is clearly dominant (>50%)
        if canonical_count <= total // 2:
            self.log_progress(
                "Date reconciliation skipped: no clear majority date.",
                level="warning"
            )
            return articles

        from datetime import timedelta
        corrected: List[Dict] = []
        for art in articles:
            dt = art.get('published_dt')
            art_date = None
            if dt and hasattr(dt, 'date'):
                art_date = dt.date()
            elif dt and hasattr(dt, 'year'):
                art_date = dt

            if art_date and art_date != canonical_date:
                diff = abs((art_date - canonical_date).days)
                if diff == 1:
                    # Reassign: replace datetime so the downstream date string changes
                    new_dt = dt.replace(
                        year=canonical_date.year,
                        month=canonical_date.month,
                        day=canonical_date.day
                    ) if hasattr(dt, 'replace') else dt
                    self.log_progress(
                        f"Date reconciled: '{art['title'][:50]}...' "
                        f"{art_date} → {canonical_date} (RSS timezone drift)",
                        level="warning"
                    )
                    art = dict(art)  # shallow copy — don't mutate shared state
                    art['published_dt'] = new_dt
                    art['published_reconciled'] = True  # flag for traceability
            corrected.append(art)

        return corrected

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
