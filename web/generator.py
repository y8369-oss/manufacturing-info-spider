"""
Static website generator module
"""
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import List
from jinja2 import Environment, FileSystemLoader

from database.models import News, Patent, Paper
from database.db_manager import DatabaseManager
from config.settings import (
    PROJECT_ROOT,
    WEB_OUTPUT_DIR,
    SITE_TITLE,
    SITE_DESCRIPTION
)

logger = logging.getLogger(__name__)


class WebsiteGenerator:
    """Static website generator class"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize website generator

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.templates_dir = PROJECT_ROOT / "web" / "templates"
        self.output_dir = WEB_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

    def generate_all(self):
        """Generate all pages"""
        logger.info("Starting website generation")

        try:
            # Get data from database
            news_list = self.db_manager.get_all_news(limit=200)
            patents_list = self.db_manager.get_all_patents(limit=200)
            papers_list = self.db_manager.get_all_papers(limit=200)

            # Generate pages
            self.generate_index(news_list, patents_list, papers_list)
            self.generate_news_page(news_list)
            self.generate_patents_page(patents_list)
            self.generate_papers_page(papers_list)

            logger.info(f"Website generated successfully at: {self.output_dir}")

        except Exception as e:
            logger.error(f"Error generating website: {e}")
            raise

    def generate_index(self, news_list: List[News],
                      patents_list: List[Patent],
                      papers_list: List[Paper]):
        """
        Generate index page

        Args:
            news_list: List of all news
            patents_list: List of all patents
            papers_list: List of all papers
        """
        template = self.env.get_template('index.html')

        # Get latest items (5 each)
        latest_news = news_list[:5]
        latest_patents = patents_list[:5]
        latest_papers = papers_list[:5]

        html = template.render(
            site_title=SITE_TITLE,
            site_description=SITE_DESCRIPTION,
            active_page='index',
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            news_count=len(news_list),
            patents_count=len(patents_list),
            papers_count=len(papers_list),
            latest_news=latest_news,
            latest_patents=latest_patents,
            latest_papers=latest_papers
        )

        output_file = self.output_dir / 'index.html'
        output_file.write_text(html, encoding='utf-8')
        logger.info(f"Generated: {output_file}")

    def generate_news_page(self, news_list: List[News]):
        """
        Generate news page

        Args:
            news_list: List of news articles
        """
        template = self.env.get_template('news.html')

        html = template.render(
            site_title=SITE_TITLE,
            site_description=SITE_DESCRIPTION,
            active_page='news',
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            news_list=news_list
        )

        output_file = self.output_dir / 'news.html'
        output_file.write_text(html, encoding='utf-8')
        logger.info(f"Generated: {output_file}")

    def generate_patents_page(self, patents_list: List[Patent]):
        """
        Generate patents page

        Args:
            patents_list: List of patents
        """
        template = self.env.get_template('patents.html')

        html = template.render(
            site_title=SITE_TITLE,
            site_description=SITE_DESCRIPTION,
            active_page='patents',
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            patents_list=patents_list
        )

        output_file = self.output_dir / 'patents.html'
        output_file.write_text(html, encoding='utf-8')
        logger.info(f"Generated: {output_file}")

    def generate_papers_page(self, papers_list: List[Paper]):
        """
        Generate papers page

        Args:
            papers_list: List of papers
        """
        template = self.env.get_template('papers.html')

        html = template.render(
            site_title=SITE_TITLE,
            site_description=SITE_DESCRIPTION,
            active_page='papers',
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            papers_list=papers_list
        )

        output_file = self.output_dir / 'papers.html'
        output_file.write_text(html, encoding='utf-8')
        logger.info(f"Generated: {output_file}")

    def copy_static_files(self):
        """Copy static files (CSS, JS, images) to output directory"""
        static_src = PROJECT_ROOT / "web" / "static"
        static_dest = self.output_dir / "static"

        if static_src.exists():
            if static_dest.exists():
                shutil.rmtree(static_dest)
            shutil.copytree(static_src, static_dest)
            logger.info(f"Copied static files to: {static_dest}")
        else:
            logger.warning(f"Static directory not found: {static_src}")

    def generate_readme(self):
        """Generate README for GitHub Pages"""
        readme_content = f"""# {SITE_TITLE}

{SITE_DESCRIPTION}

## 最后更新
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 访问网站
查看网站: [GitHub Pages链接]

## 数据来源
- 新闻: 36氪、机器人网、智能制造网等
- 专利: 国家知识产权局、百度学术
- 论文: arXiv

## 自动更新
本网站每天自动更新，内容由爬虫系统自动抓取和筛选。

---
Powered by Manufacturing Info Spider
"""

        readme_file = self.output_dir / 'README.md'
        readme_file.write_text(readme_content, encoding='utf-8')
        logger.info(f"Generated: {readme_file}")

    def clean_output_directory(self):
        """Clean output directory"""
        if self.output_dir.exists():
            for item in self.output_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info(f"Cleaned output directory: {self.output_dir}")
