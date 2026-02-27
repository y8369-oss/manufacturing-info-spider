"""
Academic paper crawler module (arXiv)
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from urllib.parse import quote

from crawlers.base_crawler import BaseCrawler
from database.models import Paper

logger = logging.getLogger(__name__)


class PaperCrawler(BaseCrawler):
    """Paper crawler class for arXiv"""

    def __init__(self):
        """Initialize paper crawler"""
        super().__init__()
        self.arxiv_api_url = "http://export.arxiv.org/api/query"
        self.arxiv_namespace = {'atom': 'http://www.w3.org/2005/Atom'}

    def crawl(self, sources: List[dict], keywords: List[str], max_results: int = 20) -> List[Paper]:
        """
        Crawl papers from multiple sources

        Args:
            sources: List of paper source configurations
            keywords: List of keywords to search
            max_results: Maximum number of results per keyword

        Returns:
            List of Paper objects
        """
        all_papers = []

        for source in sources:
            if not source.get('enabled', False):
                logger.info(f"Skipping disabled source: {source['name']}")
                continue

            logger.info(f"Crawling papers from: {source['name']}")

            try:
                if source['name'] == 'arXiv':
                    papers = self._crawl_arxiv(keywords, source.get('categories', []), max_results)
                    all_papers.extend(papers)
                    logger.info(f"Crawled {len(papers)} papers from arXiv")
                else:
                    logger.warning(f"Source {source['name']} not yet implemented")

            except Exception as e:
                logger.error(f"Error crawling {source['name']}: {e}")

        return all_papers

    def _crawl_arxiv(self, keywords: List[str], categories: List[str], max_results: int) -> List[Paper]:
        """
        Crawl papers from arXiv API

        Args:
            keywords: List of keywords to search
            categories: List of arXiv categories (e.g., cs.RO, cs.CV)
            max_results: Maximum results per keyword

        Returns:
            List of Paper objects
        """
        papers = []

        # Build search query
        # Combine keywords with OR operator
        keyword_query = ' OR '.join([f'all:{quote(kw)}' for kw in keywords[:5]])  # Limit to 5 keywords

        # Add category filter if specified
        if categories:
            category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
            search_query = f'({keyword_query}) AND ({category_query})'
        else:
            search_query = keyword_query

        # Build API URL
        # Sort by submittedDate (most recent first)
        # Get papers from the last 30 days
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        url = f"{self.arxiv_api_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        logger.info(f"Fetching arXiv papers with query: {search_query}")

        response = self.fetch_url(url)
        if not response:
            return papers

        try:
            # Parse XML response
            root = ET.fromstring(response.content)

            # Find all entry elements
            entries = root.findall('atom:entry', self.arxiv_namespace)

            for entry in entries:
                try:
                    paper = self._parse_arxiv_entry(entry)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing arXiv entry: {e}")

        except Exception as e:
            logger.error(f"Error parsing arXiv XML response: {e}")

        return papers

    def _parse_arxiv_entry(self, entry) -> Optional[Paper]:
        """
        Parse arXiv XML entry

        Args:
            entry: XML entry element

        Returns:
            Paper object or None
        """
        try:
            # Extract title
            title_elem = entry.find('atom:title', self.arxiv_namespace)
            title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else ""

            # Extract arXiv ID from entry ID
            id_elem = entry.find('atom:id', self.arxiv_namespace)
            arxiv_url = id_elem.text if id_elem is not None else ""
            arxiv_id = arxiv_url.split('/abs/')[-1] if '/abs/' in arxiv_url else ""

            # Extract authors
            author_elems = entry.findall('atom:author/atom:name', self.arxiv_namespace)
            authors = ', '.join([author.text for author in author_elems])

            # Extract abstract
            summary_elem = entry.find('atom:summary', self.arxiv_namespace)
            abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ""

            # Extract published date
            published_elem = entry.find('atom:published', self.arxiv_namespace)
            publish_date = published_elem.text[:10] if published_elem is not None else None

            # Extract PDF link
            pdf_link = ""
            link_elems = entry.findall('atom:link', self.arxiv_namespace)
            for link in link_elems:
                if link.get('title') == 'pdf':
                    pdf_link = link.get('href', '')
                    break

            # If no PDF link found, construct it from arXiv ID
            if not pdf_link and arxiv_id:
                pdf_link = f"http://arxiv.org/pdf/{arxiv_id}.pdf"

            if not title or not arxiv_id:
                return None

            return Paper(
                title=title,
                title_cn="",  # Translation can be added later
                authors=authors,
                abstract=abstract,
                abstract_cn="",  # Translation can be added later
                pdf_url=pdf_link,
                arxiv_id=arxiv_id,
                publish_date=publish_date,
                keywords=[]
            )

        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None

    def crawl_recent(self, categories: List[str], days: int = 7, max_results: int = 50) -> List[Paper]:
        """
        Crawl recent papers from specified categories

        Args:
            categories: List of arXiv categories
            days: Number of days to look back
            max_results: Maximum number of results

        Returns:
            List of Paper objects
        """
        papers = []

        # Build category query
        category_query = ' OR '.join([f'cat:{cat}' for cat in categories])

        # Build API URL
        params = {
            'search_query': category_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        url = f"{self.arxiv_api_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

        logger.info(f"Fetching recent arXiv papers from categories: {categories}")

        response = self.fetch_url(url)
        if not response:
            return papers

        try:
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', self.arxiv_namespace)

            cutoff_date = datetime.now() - timedelta(days=days)

            for entry in entries:
                try:
                    # Check if paper is within date range
                    published_elem = entry.find('atom:published', self.arxiv_namespace)
                    if published_elem is not None:
                        publish_date_str = published_elem.text[:10]
                        publish_date = datetime.strptime(publish_date_str, '%Y-%m-%d')

                        if publish_date < cutoff_date:
                            continue

                    paper = self._parse_arxiv_entry(entry)
                    if paper:
                        papers.append(paper)

                except Exception as e:
                    logger.error(f"Error parsing arXiv entry: {e}")

        except Exception as e:
            logger.error(f"Error parsing arXiv XML response: {e}")

        return papers
