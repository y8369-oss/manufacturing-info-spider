"""
Keyword filter module for content filtering
"""
import logging
from typing import List, Tuple, Dict, Any
from database.models import News, Patent, Paper

logger = logging.getLogger(__name__)


class KeywordFilter:
    """Keyword filter class"""

    def __init__(self, keywords_config: Dict[str, Any]):
        """
        Initialize keyword filter

        Args:
            keywords_config: Dictionary containing keywords configuration
        """
        self.keywords_config = keywords_config
        self.news_keywords = self._flatten_keywords(keywords_config.get('news', {}))
        self.patent_keywords = keywords_config.get('patents', [])
        self.paper_keywords = keywords_config.get('papers', [])
        self.settings = keywords_config.get('settings', {})

    def _flatten_keywords(self, keyword_dict: Dict[str, List[str]]) -> List[str]:
        """
        Flatten nested keyword dictionary to a single list

        Args:
            keyword_dict: Dictionary of keyword categories

        Returns:
            Flattened list of keywords
        """
        keywords = []
        for category, kws in keyword_dict.items():
            keywords.extend(kws)
        return keywords

    def filter_news(self, news_list: List[News], threshold: int = None) -> List[News]:
        """
        Filter news articles by keywords

        Args:
            news_list: List of News objects
            threshold: Minimum keyword matches required (default from config)

        Returns:
            List of filtered News objects with scores and matched keywords
        """
        if threshold is None:
            threshold = self.settings.get('news_threshold', 1)

        filtered_news = []

        for news in news_list:
            # Combine title and summary for matching
            content = f"{news.title} {news.summary}".lower()

            # Match keywords
            matched, score, matched_keywords = self._match_keywords(content, self.news_keywords)

            if matched and score >= threshold:
                news.score = score
                news.keywords = matched_keywords
                filtered_news.append(news)
                logger.debug(f"News matched: {news.title[:50]}... (score: {score})")

        logger.info(f"Filtered {len(filtered_news)} news from {len(news_list)} total")
        return filtered_news

    def filter_patents(self, patent_list: List[Patent], threshold: int = None) -> List[Patent]:
        """
        Filter patents by keywords

        Args:
            patent_list: List of Patent objects
            threshold: Minimum keyword matches required

        Returns:
            List of filtered Patent objects with matched keywords
        """
        if threshold is None:
            threshold = self.settings.get('patent_threshold', 1)

        filtered_patents = []

        for patent in patent_list:
            # Combine title and abstract for matching
            content = f"{patent.title} {patent.abstract}".lower()

            # Match keywords
            matched, score, matched_keywords = self._match_keywords(content, self.patent_keywords)

            if matched and score >= threshold:
                patent.keywords = matched_keywords
                filtered_patents.append(patent)
                logger.debug(f"Patent matched: {patent.title[:50]}... (score: {score})")

        logger.info(f"Filtered {len(filtered_patents)} patents from {len(patent_list)} total")
        return filtered_patents

    def filter_papers(self, paper_list: List[Paper], threshold: int = None) -> List[Paper]:
        """
        Filter papers by keywords

        Args:
            paper_list: List of Paper objects
            threshold: Minimum keyword matches required

        Returns:
            List of filtered Paper objects with matched keywords
        """
        if threshold is None:
            threshold = self.settings.get('paper_threshold', 1)

        filtered_papers = []

        for paper in paper_list:
            # Combine title and abstract for matching
            content = f"{paper.title} {paper.abstract}".lower()

            # Match keywords
            matched, score, matched_keywords = self._match_keywords(content, self.paper_keywords)

            if matched and score >= threshold:
                paper.keywords = matched_keywords
                filtered_papers.append(paper)
                logger.debug(f"Paper matched: {paper.title[:50]}... (score: {score})")

        logger.info(f"Filtered {len(filtered_papers)} papers from {len(paper_list)} total")
        return filtered_papers

    def _match_keywords(self, content: str, keywords: List[str]) -> Tuple[bool, int, List[str]]:
        """
        Match keywords in content

        Args:
            content: Text content to search (should be lowercase)
            keywords: List of keywords to match

        Returns:
            Tuple of (matched: bool, score: int, matched_keywords: List[str])
        """
        score = 0
        matched_keywords = []

        for keyword in keywords:
            # Convert keyword to lowercase for case-insensitive matching
            kw_lower = keyword.lower()

            if kw_lower in content:
                score += 1
                matched_keywords.append(keyword)

        matched = score > 0

        return matched, score, matched_keywords

    def filter_by_category(self, news_list: List[News], category: str) -> List[News]:
        """
        Filter news by specific keyword category

        Args:
            news_list: List of News objects
            category: Category name (e.g., 'robot', 'ai_tech')

        Returns:
            List of filtered News objects
        """
        category_keywords = self.keywords_config.get('news', {}).get(category, [])

        if not category_keywords:
            logger.warning(f"Category '{category}' not found in keywords config")
            return []

        filtered_news = []

        for news in news_list:
            content = f"{news.title} {news.summary}".lower()
            matched, score, matched_keywords = self._match_keywords(content, category_keywords)

            if matched:
                news.score = score
                news.keywords = matched_keywords
                filtered_news.append(news)

        logger.info(f"Filtered {len(filtered_news)} news for category '{category}'")
        return filtered_news

    def get_top_scored(self, news_list: List[News], top_n: int = 10) -> List[News]:
        """
        Get top N news articles by score

        Args:
            news_list: List of News objects with scores
            top_n: Number of top items to return

        Returns:
            List of top scored News objects
        """
        # Sort by score (descending) and then by created_at (newest first)
        sorted_news = sorted(news_list, key=lambda x: (x.score, x.created_at), reverse=True)
        return sorted_news[:top_n]

    def get_keyword_statistics(self, items: List[Any]) -> Dict[str, int]:
        """
        Get statistics of keyword matches

        Args:
            items: List of items (News, Patent, or Paper) with keywords attribute

        Returns:
            Dictionary of keyword -> count
        """
        keyword_counts = {}

        for item in items:
            if hasattr(item, 'keywords') and item.keywords:
                for keyword in item.keywords:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Sort by count (descending)
        sorted_keywords = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))

        return sorted_keywords
