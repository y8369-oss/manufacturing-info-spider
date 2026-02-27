"""
News crawler module
"""
import logging
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from crawlers.base_crawler import BaseCrawler
from database.models import News

logger = logging.getLogger(__name__)


class NewsCrawler(BaseCrawler):
    """News crawler class"""

    def __init__(self):
        """Initialize news crawler"""
        super().__init__()

    def crawl(self, sources: List[dict], keywords: List[str]) -> List[News]:
        """
        Crawl news from multiple sources

        Args:
            sources: List of news source configurations
            keywords: List of keywords to search

        Returns:
            List of News objects
        """
        all_news = []

        for source in sources:
            if not source.get('enabled', False):
                logger.info(f"Skipping disabled source: {source['name']}")
                continue

            logger.info(f"Crawling news from: {source['name']}")

            try:
                if source.get('type') == 'api':
                    news_items = self._crawl_api_source(source, keywords)
                else:
                    news_items = self._crawl_html_source(source, keywords)

                all_news.extend(news_items)
                logger.info(f"Crawled {len(news_items)} news from {source['name']}")

            except Exception as e:
                logger.error(f"Error crawling {source['name']}: {e}")

        return all_news

    def _crawl_api_source(self, source: dict, keywords: List[str]) -> List[News]:
        """
        Crawl news from API source (e.g., 36Kr)

        Args:
            source: Source configuration
            keywords: Keywords to search

        Returns:
            List of News objects
        """
        news_items = []

        # For 36Kr, we'll search for each keyword
        for keyword in keywords[:5]:  # Limit to 5 keywords to avoid too many requests
            search_url = source['search_url'].format(keyword=keyword)

            # 36Kr uses an API endpoint, adjust URL accordingly
            # Note: This is a simplified implementation
            # Real 36Kr API might need authentication or different endpoint
            response = self.fetch_url(search_url)

            if not response:
                continue

            try:
                # Try to parse as HTML first (since 36Kr might return HTML)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find article elements (adjust selectors based on actual site structure)
                articles = soup.find_all('div', class_=['article-item', 'newsflash-item'])

                for article in articles[:5]:  # Limit to 5 articles per keyword
                    try:
                        news = self._parse_36kr_article(article, source['name'])
                        if news:
                            news_items.append(news)
                    except Exception as e:
                        logger.error(f"Error parsing article: {e}")

            except Exception as e:
                logger.error(f"Error processing response from {source['name']}: {e}")

        return news_items

    def _parse_36kr_article(self, article, source_name: str) -> Optional[News]:
        """
        Parse 36Kr article element

        Args:
            article: BeautifulSoup article element
            source_name: Name of the source

        Returns:
            News object or None
        """
        try:
            # Extract title and URL
            title_elem = article.find(['h3', 'h2', 'a'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')

            if not url:
                link_elem = article.find('a')
                url = link_elem.get('href', '') if link_elem else ''

            # Make URL absolute
            if url and not url.startswith('http'):
                url = f"https://www.36kr.com{url}"

            # Extract summary
            summary_elem = article.find(['p', 'div'], class_=['summary', 'article-desc'])
            summary = summary_elem.get_text(strip=True) if summary_elem else ""

            # Extract publish date (if available)
            date_elem = article.find(['time', 'span'], class_=['time', 'date'])
            publish_date = date_elem.get_text(strip=True) if date_elem else None

            if not title or not url:
                return None

            return News(
                title=title,
                url=url,
                source=source_name,
                publish_date=publish_date,
                summary=summary,
                content="",
                keywords=[],
                score=0
            )

        except Exception as e:
            logger.error(f"Error parsing 36Kr article: {e}")
            return None

    def _crawl_html_source(self, source: dict, keywords: List[str]) -> List[News]:
        """
        Crawl news from HTML source

        Args:
            source: Source configuration
            keywords: Keywords (not used for HTML sources, they browse latest news)

        Returns:
            List of News objects
        """
        news_items = []

        # Fetch the news page
        url = source.get('search_url', source['base_url'])
        response = self.fetch_url(url)

        if not response:
            return news_items

        try:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple selector strategies
            articles = []

            # Strategy 1: Look for common article containers
            articles = soup.find_all(['article', 'div'], class_=['news-item', 'article', 'post', 'item'])

            if not articles:
                # Strategy 2: Look for list items
                articles = soup.find_all('li', class_=['list-item', 'news', 'item'])

            if not articles:
                # Strategy 3: Look for divs with 'news' or 'article' in class name
                all_divs = soup.find_all('div', class_=True)
                articles = [d for d in all_divs if any(kw in ' '.join(d.get('class', [])).lower()
                           for kw in ['news', 'article', 'post', 'item', 'card'])][:20]

            if not articles:
                # Strategy 4: Find all links with titles
                links_with_titles = soup.find_all('a', href=True)
                # Filter links that look like article links
                articles = [link.parent for link in links_with_titles
                           if link.get_text(strip=True) and len(link.get_text(strip=True)) > 10][:20]

            logger.debug(f"Found {len(articles)} potential articles")

            for article in articles[:20]:  # Limit to 20 articles
                try:
                    news = self._parse_generic_article(article, source['name'], source['base_url'])
                    if news:
                        news_items.append(news)
                except Exception as e:
                    logger.debug(f"Error parsing article from {source['name']}: {e}")

        except Exception as e:
            logger.error(f"Error processing HTML from {source['name']}: {e}")

        return news_items

    def _parse_generic_article(self, article, source_name: str, base_url: str) -> Optional[News]:
        """
        Parse generic article element

        Args:
            article: BeautifulSoup article element
            source_name: Name of the source
            base_url: Base URL for making absolute URLs

        Returns:
            News object or None
        """
        try:
            # Find title and URL
            title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=['title', 'heading'])
            if not title_elem:
                title_elem = article.find('a')

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')

            if not url:
                link_elem = article.find('a')
                url = link_elem.get('href', '') if link_elem else ''

            # Make URL absolute
            if url and not url.startswith('http'):
                if url.startswith('/'):
                    url = f"{base_url}{url}"
                else:
                    url = f"{base_url}/{url}"

            # Extract summary/description
            summary_elem = article.find(['p', 'div'], class_=['summary', 'desc', 'description', 'excerpt'])
            summary = summary_elem.get_text(strip=True) if summary_elem else ""

            # Extract date
            date_elem = article.find(['time', 'span'], class_=['date', 'time', 'publish-time'])
            publish_date = None
            if date_elem:
                publish_date = date_elem.get_text(strip=True)
                # Also check for datetime attribute
                if not publish_date and date_elem.get('datetime'):
                    publish_date = date_elem['datetime']

            if not title or not url:
                return None

            return News(
                title=title,
                url=url,
                source=source_name,
                publish_date=publish_date,
                summary=summary,
                content="",
                keywords=[],
                score=0
            )

        except Exception as e:
            logger.error(f"Error parsing generic article: {e}")
            return None

    def crawl_single_source(self, source: dict, max_items: int = 20) -> List[News]:
        """
        Crawl news from a single source without keyword filtering

        Args:
            source: Source configuration
            max_items: Maximum number of items to crawl

        Returns:
            List of News objects
        """
        logger.info(f"Crawling news from: {source['name']}")

        try:
            url = source.get('search_url', source['base_url'])
            response = self.fetch_url(url)

            if not response:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple selectors
            articles = (
                soup.find_all(['article', 'div'], class_=['news-item', 'article', 'post'], limit=max_items) or
                soup.find_all('li', class_=['list-item', 'news'], limit=max_items) or
                soup.find_all('div', class_=['item'], limit=max_items)
            )

            news_items = []
            for article in articles:
                news = self._parse_generic_article(article, source['name'], source['base_url'])
                if news:
                    news_items.append(news)

            logger.info(f"Crawled {len(news_items)} news from {source['name']}")
            return news_items

        except Exception as e:
            logger.error(f"Error crawling {source['name']}: {e}")
            return []
