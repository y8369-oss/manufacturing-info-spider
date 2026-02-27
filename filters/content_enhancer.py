"""
Content enhancer module for extracting companies and enriching content
"""
import logging
import re
from typing import List, Tuple, Set
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ContentEnhancer:
    """Content enhancer for extracting companies and enriching information"""

    def __init__(self, keywords_config: dict):
        """Initialize content enhancer with keywords configuration"""
        self.companies = keywords_config.get('companies', [])

    def extract_companies(self, text: str) -> List[str]:
        """
        Extract company names from text

        Args:
            text: Text to extract companies from

        Returns:
            List of company names found
        """
        companies_found = []
        text_lower = text.lower()

        # Check predefined company list
        for company in self.companies:
            if company.lower() in text_lower:
                companies_found.append(company)

        # Extract companies with common suffixes (Chinese)
        company_pattern = r'[\u4e00-\u9fa5]{2,10}(科技|智能|机器人|汽车|制造|集团|公司)'
        matches = re.findall(company_pattern, text)

        for match in matches:
            # Reconstruct full company name
            # Find the match in original text to preserve exact casing
            match_pattern = re.escape(match)
            full_matches = re.findall(r'[\u4e00-\u9fa5]{2,10}' + match_pattern, text)
            if full_matches:
                full_company = full_matches[0]
                if full_company not in companies_found:
                    companies_found.append(full_company)

        return list(set(companies_found))  # Remove duplicates

    def generate_summary(self, title: str, content: str, max_length: int = 150) -> str:
        """
        Generate summary from title and content

        Args:
            title: Article title
            content: Article content
            max_length: Maximum summary length

        Returns:
            Summary text
        """
        # If content is provided and long enough, use it
        if content and len(content) > 20:
            summary = content[:max_length]
            if len(content) > max_length:
                summary += "..."
            return summary

        # Otherwise, use title as summary
        return title

    def enrich_news(self, news_item) -> None:
        """
        Enrich news item with extracted information

        Args:
            news_item: News object to enrich (modified in place)
        """
        # Extract companies from title and summary
        text = f"{news_item.title} {news_item.summary}"
        companies = self.extract_companies(text)

        # Add companies to keywords if not already there
        if companies:
            # Create a set of existing keywords
            existing_keywords = set(news_item.keywords) if news_item.keywords else set()

            # Add companies that aren't already in keywords
            for company in companies:
                if company not in existing_keywords:
                    existing_keywords.add(company)

            news_item.keywords = list(existing_keywords)

    def enrich_paper(self, paper_item) -> None:
        """
        Enrich paper item (placeholder for future translation)

        Args:
            paper_item: Paper object to enrich (modified in place)
        """
        # For now, just ensure keywords are set
        if not paper_item.keywords:
            paper_item.keywords = []

    def enrich_patent(self, patent_item) -> None:
        """
        Enrich patent item with extracted information

        Args:
            patent_item: Patent object to enrich (modified in place)
        """
        # Extract companies from applicant field
        if patent_item.applicant:
            companies = self.extract_companies(patent_item.applicant)

            # Add to keywords
            existing_keywords = set(patent_item.keywords) if patent_item.keywords else set()
            for company in companies:
                existing_keywords.add(company)

            patent_item.keywords = list(existing_keywords)
