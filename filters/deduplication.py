"""
Deduplication module for removing duplicate items
"""
import logging
from typing import List, Set
from database.models import News, Patent, Paper
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class Deduplicator:
    """Deduplicator class for removing duplicates"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize deduplicator

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def deduplicate_news(self, news_list: List[News]) -> List[News]:
        """
        Remove duplicate news articles based on URL

        Args:
            news_list: List of News objects

        Returns:
            List of deduplicated News objects
        """
        unique_news = []
        seen_urls = set()

        for news in news_list:
            # Check if URL already seen in current list
            if news.url in seen_urls:
                logger.debug(f"Skipping duplicate URL in list: {news.url}")
                continue

            # Check if URL exists in database
            if self.db_manager.url_exists(news.url):
                logger.debug(f"Skipping existing URL in database: {news.url}")
                continue

            seen_urls.add(news.url)
            unique_news.append(news)

        removed_count = len(news_list) - len(unique_news)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate news articles")

        return unique_news

    def deduplicate_patents(self, patent_list: List[Patent]) -> List[Patent]:
        """
        Remove duplicate patents based on application number

        Args:
            patent_list: List of Patent objects

        Returns:
            List of deduplicated Patent objects
        """
        unique_patents = []
        seen_application_nos = set()

        for patent in patent_list:
            # Check if application number already seen in current list
            if patent.application_no in seen_application_nos:
                logger.debug(f"Skipping duplicate application number in list: {patent.application_no}")
                continue

            # Check if application number exists in database
            if self.db_manager.patent_exists(patent.application_no):
                logger.debug(f"Skipping existing patent in database: {patent.application_no}")
                continue

            seen_application_nos.add(patent.application_no)
            unique_patents.append(patent)

        removed_count = len(patent_list) - len(unique_patents)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate patents")

        return unique_patents

    def deduplicate_papers(self, paper_list: List[Paper]) -> List[Paper]:
        """
        Remove duplicate papers based on arXiv ID

        Args:
            paper_list: List of Paper objects

        Returns:
            List of deduplicated Paper objects
        """
        unique_papers = []
        seen_arxiv_ids = set()

        for paper in paper_list:
            # Skip if no arXiv ID
            if not paper.arxiv_id:
                logger.warning(f"Paper without arXiv ID: {paper.title[:50]}...")
                continue

            # Check if arXiv ID already seen in current list
            if paper.arxiv_id in seen_arxiv_ids:
                logger.debug(f"Skipping duplicate arXiv ID in list: {paper.arxiv_id}")
                continue

            # Check if arXiv ID exists in database
            if self.db_manager.paper_exists(paper.arxiv_id):
                logger.debug(f"Skipping existing paper in database: {paper.arxiv_id}")
                continue

            seen_arxiv_ids.add(paper.arxiv_id)
            unique_papers.append(paper)

        removed_count = len(paper_list) - len(unique_papers)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate papers")

        return unique_papers

    def deduplicate_by_title(self, items: List[any], threshold: float = 0.9) -> List[any]:
        """
        Remove duplicates based on title similarity (fuzzy matching)

        Args:
            items: List of items with title attribute
            threshold: Similarity threshold (0-1)

        Returns:
            List of deduplicated items
        """
        # This is a simple implementation using exact title matching
        # For fuzzy matching, consider using libraries like difflib or fuzzywuzzy

        unique_items = []
        seen_titles = set()

        for item in items:
            # Normalize title (lowercase, strip whitespace)
            normalized_title = item.title.lower().strip()

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_items.append(item)
            else:
                logger.debug(f"Skipping duplicate title: {item.title[:50]}...")

        removed_count = len(items) - len(unique_items)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} items with duplicate titles")

        return unique_items

    def get_duplicate_stats(self, news_urls: List[str] = None,
                          patent_nos: List[str] = None,
                          arxiv_ids: List[str] = None) -> dict:
        """
        Get statistics about duplicates

        Args:
            news_urls: List of news URLs to check
            patent_nos: List of patent application numbers to check
            arxiv_ids: List of arXiv IDs to check

        Returns:
            Dictionary with duplicate statistics
        """
        stats = {
            'news_duplicates': 0,
            'patent_duplicates': 0,
            'paper_duplicates': 0
        }

        if news_urls:
            for url in news_urls:
                if self.db_manager.url_exists(url):
                    stats['news_duplicates'] += 1

        if patent_nos:
            for patent_no in patent_nos:
                if self.db_manager.patent_exists(patent_no):
                    stats['patent_duplicates'] += 1

        if arxiv_ids:
            for arxiv_id in arxiv_ids:
                if self.db_manager.paper_exists(arxiv_id):
                    stats['paper_duplicates'] += 1

        return stats
