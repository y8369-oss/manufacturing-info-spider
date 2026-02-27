"""
Base crawler class with error handling and retry logic
"""
import time
import random
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import (
    USER_AGENTS,
    REQUEST_TIMEOUT,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    MAX_RETRIES
)

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """Base crawler class"""

    def __init__(self):
        """Initialize crawler"""
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get random headers"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _random_delay(self):
        """Add random delay to avoid being blocked"""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    def fetch_url(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Fetch URL with error handling

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests

        Returns:
            Response object or None if failed
        """
        try:
            # Add random delay
            self._random_delay()

            # Set default headers if not provided
            if 'headers' not in kwargs:
                kwargs['headers'] = self._get_headers()

            # Set timeout if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = REQUEST_TIMEOUT

            # Make request
            logger.info(f"Fetching {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def fetch_json(self, url: str, method: str = 'GET', **kwargs) -> Optional[Dict[Any, Any]]:
        """
        Fetch JSON data from URL

        Args:
            url: URL to fetch
            method: HTTP method
            **kwargs: Additional arguments

        Returns:
            JSON data as dictionary or None if failed
        """
        response = self.fetch_url(url, method, **kwargs)
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Error parsing JSON from {url}: {e}")
                return None
        return None

    @abstractmethod
    def crawl(self, **kwargs):
        """
        Main crawl method to be implemented by subclasses

        Args:
            **kwargs: Crawler-specific arguments

        Returns:
            List of crawled items
        """
        pass

    def close(self):
        """Close session"""
        if self.session:
            self.session.close()
            logger.info(f"{self.__class__.__name__} session closed")

    def __enter__(self):
        """Context manager enter"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
