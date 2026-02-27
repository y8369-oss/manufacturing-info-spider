"""
Feishu bot notifier module
"""
import json
import logging
import hmac
import hashlib
import base64
import time
from typing import List, Dict, Any, Optional
import requests

from database.models import News, Patent, Paper
from config.settings import FEISHU_WEBHOOK_URL, FEISHU_SECRET

logger = logging.getLogger(__name__)


class FeishuBot:
    """Feishu bot class for sending messages"""

    def __init__(self, webhook_url: str = None, secret: str = None):
        """
        Initialize Feishu bot

        Args:
            webhook_url: Feishu webhook URL
            secret: Feishu webhook secret for signature
        """
        self.webhook_url = webhook_url or FEISHU_WEBHOOK_URL
        self.secret = secret or FEISHU_SECRET

        if not self.webhook_url:
            logger.warning("Feishu webhook URL not configured")

    def _generate_signature(self, timestamp: int) -> str:
        """
        Generate signature for Feishu webhook

        Args:
            timestamp: Current timestamp

        Returns:
            Base64 encoded signature
        """
        if not self.secret:
            return ""

        # Construct string to sign
        string_to_sign = f"{timestamp}\n{self.secret}"

        # Generate HMAC-SHA256 signature
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        # Base64 encode
        signature = base64.b64encode(hmac_code).decode('utf-8')

        return signature

    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send message to Feishu

        Args:
            message: Message payload

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Feishu webhook URL not configured")
            return False

        try:
            # Add signature if secret is configured
            if self.secret:
                timestamp = int(time.time())
                signature = self._generate_signature(timestamp)
                message['timestamp'] = str(timestamp)
                message['sign'] = signature

            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 0 or result.get('StatusCode') == 0:
                logger.info("Message sent to Feishu successfully")
                return True
            else:
                logger.error(f"Failed to send message to Feishu: {result}")
                return False

        except Exception as e:
            logger.error(f"Error sending message to Feishu: {e}")
            return False

    def send_news(self, news: News) -> bool:
        """
        Send single news article to Feishu

        Args:
            news: News object

        Returns:
            True if successful
        """
        card = self._create_news_card([news])
        message = {
            "msg_type": "interactive",
            "card": card
        }
        return self.send_message(message)

    def send_news_batch(self, news_list: List[News]) -> bool:
        """
        Send multiple news articles to Feishu

        Args:
            news_list: List of News objects

        Returns:
            True if successful
        """
        if not news_list:
            logger.warning("No news to send")
            return False

        card = self._create_news_card(news_list)
        message = {
            "msg_type": "interactive",
            "card": card
        }
        return self.send_message(message)

    def send_papers_and_patents(self, papers: List[Paper], patents: List[Patent]) -> bool:
        """
        Send papers and patents in a single message

        Args:
            papers: List of Paper objects
            patents: List of Patent objects

        Returns:
            True if successful
        """
        if not papers and not patents:
            logger.warning("No papers or patents to send")
            return False

        card = self._create_papers_patents_card(papers, patents)
        message = {
            "msg_type": "interactive",
            "card": card
        }
        return self.send_message(message)

    def _create_news_card(self, news_list: List[News]) -> Dict[str, Any]:
        """
        Create Feishu card for news

        Args:
            news_list: List of News objects

        Returns:
            Card JSON
        """
        elements = []

        for i, news in enumerate(news_list):
            # Separate keywords into technical and companies
            tech_keywords = []
            companies = []

            if news.keywords:
                # Simple heuristic: if keyword contains company suffixes, it's likely a company
                company_suffixes = ['公司', '科技', '汽车', '集团', '机器人', '智能']
                for kw in news.keywords:
                    is_company = any(suffix in kw for suffix in company_suffixes)
                    # Also check if it starts with capital letter (for English companies)
                    is_company = is_company or (len(kw) > 1 and kw[0].isupper() and ' ' not in kw)

                    if is_company:
                        companies.append(kw)
                    else:
                        tech_keywords.append(kw)

            # Build content
            content = f"**📄 {news.title}**\n\n"

            # Source and date
            content += f"**来源**: {news.source}"
            if news.publish_date:
                content += f" | **发布**: {news.publish_date}"
            content += "\n\n"

            # Technical keywords
            if tech_keywords:
                tech_str = " ".join([f"#{kw}" for kw in tech_keywords])
                content += f"**技术关键词**: {tech_str}\n"

            # Companies
            if companies:
                company_str = " ".join([f"🏢{c}" for c in companies])
                content += f"**相关企业**: {company_str}\n"

            # Summary
            if news.summary:
                content += f"\n**内容简介**:\n"
                summary = news.summary[:180] if len(news.summary) > 180 else news.summary
                content += f"{summary}{'...' if len(news.summary) > 180 else ''}\n"

            # Link
            content += f"\n[🔗 查看详情]({news.url})"

            elements.append({
                "tag": "markdown",
                "content": content
            })

            # Add divider between items (except for last item)
            if i < len(news_list) - 1:
                elements.append({
                    "tag": "hr"
                })

        card = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📰 制造业新闻资讯 ({len(news_list)}条)"
                },
                "template": "blue"
            },
            "elements": elements
        }

        return card

    def _create_papers_patents_card(self, papers: List[Paper], patents: List[Patent]) -> Dict[str, Any]:
        """
        Create Feishu card for papers and patents

        Args:
            papers: List of Paper objects
            patents: List of Patent objects

        Returns:
            Card JSON
        """
        elements = []

        # Add papers section
        if papers:
            elements.append({
                "tag": "markdown",
                "content": f"### 📚 学术论文 ({len(papers)}篇)"
            })

            for i, paper in enumerate(papers):
                # Build content
                content = f"**{paper.title}**\n\n"

                # Authors
                content += f"**作者**: {paper.authors[:100]}{'...' if len(paper.authors) > 100 else ''}\n"

                # Link
                if paper.pdf_url:
                    content += f"**链接**: [📄 PDF]({paper.pdf_url})\n"

                # Keywords
                if paper.keywords:
                    keywords_str = " ".join([f"#{kw}" for kw in paper.keywords[:6]])  # Limit keywords
                    content += f"**关键词**: {keywords_str}\n"

                # Abstract
                if paper.abstract:
                    content += f"\n**摘要**:\n"
                    abstract = paper.abstract[:200] if len(paper.abstract) > 200 else paper.abstract
                    content += f"{abstract}{'...' if len(paper.abstract) > 200 else ''}"

                elements.append({
                    "tag": "markdown",
                    "content": content
                })

                if i < len(papers) - 1:
                    elements.append({"tag": "hr"})

        # Add divider between sections
        if papers and patents:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": "\n"
                }
            })

        # Add patents section
        if patents:
            elements.append({
                "tag": "markdown",
                "content": f"### 🔬 专利信息 ({len(patents)}项)"
            })

            for i, patent in enumerate(patents):
                # Build content
                content = f"**{patent.title}**\n\n"

                # Applicant
                if patent.applicant:
                    content += f"**权利人**: {patent.applicant}\n"

                # Application number and link
                content += f"**申请号**: {patent.application_no}\n"

                # Keywords
                if patent.keywords:
                    keywords_str = " ".join([f"#{kw}" for kw in patent.keywords[:6]])
                    content += f"**关键词**: {keywords_str}\n"

                # Abstract
                if patent.abstract:
                    content += f"\n**摘要**:\n"
                    abstract = patent.abstract[:200] if len(patent.abstract) > 200 else patent.abstract
                    content += f"{abstract}{'...' if len(patent.abstract) > 200 else ''}"

                elements.append({
                    "tag": "markdown",
                    "content": content
                })

                if i < len(patents) - 1:
                    elements.append({"tag": "hr"})

        card = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📑 每周文献与专利汇总"
                },
                "template": "green"
            },
            "elements": elements
        }

        return card

    def send_text(self, text: str) -> bool:
        """
        Send plain text message

        Args:
            text: Text message

        Returns:
            True if successful
        """
        message = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        return self.send_message(message)

    def send_error_notification(self, error_message: str, context: str = "") -> bool:
        """
        Send error notification

        Args:
            error_message: Error message
            context: Additional context information

        Returns:
            True if successful
        """
        text = f"⚠️ 爬虫系统错误通知\n\n"
        text += f"错误信息: {error_message}\n"
        if context:
            text += f"上下文: {context}\n"
        text += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_text(text)
