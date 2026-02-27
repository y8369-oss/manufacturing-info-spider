"""
Patent crawler module
"""
import logging
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re

from crawlers.base_crawler import BaseCrawler
from database.models import Patent

logger = logging.getLogger(__name__)


class PatentCrawler(BaseCrawler):
    """Patent crawler class"""

    def __init__(self):
        """Initialize patent crawler"""
        super().__init__()

    def crawl(self, sources: List[dict], keywords: List[str]) -> List[Patent]:
        """
        Crawl patents from multiple sources

        Args:
            sources: List of patent source configurations
            keywords: List of keywords to search

        Returns:
            List of Patent objects
        """
        all_patents = []

        for source in sources:
            if not source.get('enabled', False):
                logger.info(f"Skipping disabled source: {source['name']}")
                continue

            logger.info(f"Crawling patents from: {source['name']}")

            try:
                if source.get('type') == 'api':
                    patents = self._crawl_api_source(source, keywords)
                else:
                    patents = self._crawl_html_source(source, keywords)

                all_patents.extend(patents)
                logger.info(f"Crawled {len(patents)} patents from {source['name']}")

            except Exception as e:
                logger.error(f"Error crawling {source['name']}: {e}")

        return all_patents

    def _crawl_api_source(self, source: dict, keywords: List[str]) -> List[Patent]:
        """
        Crawl patents from API source (e.g., CNIPA)

        Args:
            source: Source configuration
            keywords: Keywords to search

        Returns:
            List of Patent objects
        """
        patents = []

        # Note: CNIPA API requires complex authentication and POST requests
        # This is a simplified placeholder implementation
        # Real implementation would need to:
        # 1. Handle CNIPA's authentication
        # 2. Construct proper search queries
        # 3. Parse XML/JSON responses

        logger.warning(f"API crawling for {source['name']} requires additional implementation")

        # For now, return empty list
        # In production, implement proper CNIPA API integration
        return patents

    def _crawl_html_source(self, source: dict, keywords: List[str]) -> List[Patent]:
        """
        Crawl patents from HTML source (e.g., Baidu Scholar)

        Args:
            source: Source configuration
            keywords: Keywords to search

        Returns:
            List of Patent objects
        """
        patents = []

        # Search for each keyword (limit to avoid too many requests)
        for keyword in keywords[:3]:
            search_url = source['search_url'].format(keyword=keyword)
            response = self.fetch_url(search_url)

            if not response:
                continue

            try:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find patent results
                # Baidu Scholar uses 'result' class for search results
                results = soup.find_all('div', class_=['result', 'c-result'])

                for result in results[:10]:  # Limit to 10 per keyword
                    try:
                        patent = self._parse_baidu_patent(result)
                        if patent:
                            patents.append(patent)
                    except Exception as e:
                        logger.error(f"Error parsing patent result: {e}")

            except Exception as e:
                logger.error(f"Error processing patents from {source['name']}: {e}")

        return patents

    def _parse_baidu_patent(self, result) -> Optional[Patent]:
        """
        Parse Baidu Scholar patent result

        Args:
            result: BeautifulSoup result element

        Returns:
            Patent object or None
        """
        try:
            # Extract title
            title_elem = result.find(['h3', 'a'], class_=['t', 'title'])
            if not title_elem:
                title_elem = result.find('a')

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            # Extract abstract/description
            abstract_elem = result.find(['div', 'p'], class_=['c-abstract', 'abstract'])
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

            # Try to extract patent number from text
            text = result.get_text()
            application_no = self._extract_patent_number(text)

            if not application_no:
                # Generate a unique identifier from title hash
                application_no = f"TEMP_{abs(hash(title)) % 10000000000}"

            # Extract applicant and date info
            meta_elem = result.find(['div', 'p'], class_=['meta', 'c-row'])
            applicant = ""
            application_date = None

            if meta_elem:
                meta_text = meta_elem.get_text()

                # Try to extract applicant
                applicant_match = re.search(r'申请人[：:]\s*([^，,;；\n]+)', meta_text)
                if applicant_match:
                    applicant = applicant_match.group(1).strip()

                # Try to extract date
                date_match = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2})', meta_text)
                if date_match:
                    application_date = date_match.group(1)

            return Patent(
                title=title,
                application_no=application_no,
                publication_no="",
                application_date=application_date,
                publication_date=None,
                applicant=applicant,
                inventor="",
                abstract=abstract,
                keywords=[]
            )

        except Exception as e:
            logger.error(f"Error parsing Baidu patent: {e}")
            return None

    def _extract_patent_number(self, text: str) -> Optional[str]:
        """
        Extract patent number from text

        Args:
            text: Text containing patent number

        Returns:
            Patent number or None
        """
        # Chinese patent numbers format: CN + digits + type letter
        # Example: CN201910123456.7
        patterns = [
            r'CN\d{12,}[A-Z]?',  # CN patent number
            r'[申请公开公告]号[：:]\s*([A-Z]{2}\d+[A-Z]?)',  # With prefix
            r'\b\d{15,}\b'  # Just numbers
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0) if 'CN' in match.group(0) else match.group(1) if len(match.groups()) > 0 else match.group(0)

        return None

    def crawl_keywords(self, source: dict, keywords: List[str], max_per_keyword: int = 5) -> List[Patent]:
        """
        Crawl patents for specific keywords

        Args:
            source: Source configuration
            keywords: List of keywords
            max_per_keyword: Maximum patents per keyword

        Returns:
            List of Patent objects
        """
        patents = []

        for keyword in keywords:
            logger.info(f"Searching patents for keyword: {keyword}")

            search_url = source['search_url'].format(keyword=keyword)
            response = self.fetch_url(search_url)

            if not response:
                continue

            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=['result', 'c-result'], limit=max_per_keyword)

                for result in results:
                    patent = self._parse_baidu_patent(result)
                    if patent:
                        patents.append(patent)

            except Exception as e:
                logger.error(f"Error crawling keyword '{keyword}': {e}")

        return patents
