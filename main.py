#!/usr/bin/env python3
"""
Manufacturing Info Spider - Main Entry Point
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    DATABASE_PATH,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    NEWS_PER_WEEK,
    PAPERS_PER_WEEK,
    PATENTS_PER_WEEK
)
from database.db_manager import DatabaseManager
from crawlers.news_crawler import NewsCrawler
from crawlers.patent_crawler import PatentCrawler
from crawlers.paper_crawler import PaperCrawler
from filters.keyword_filter import KeywordFilter
from filters.deduplication import Deduplicator
from notifiers.feishu_bot import FeishuBot
from web.generator import WebsiteGenerator
from scheduler.task_scheduler import TaskScheduler

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_file: Path):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config {config_file}: {e}")
        return {}


def crawl_news(db_manager: DatabaseManager, feishu_bot: FeishuBot,
               dry_run: bool = False, test: bool = False):
    """
    Crawl and process news

    Args:
        db_manager: Database manager
        feishu_bot: Feishu bot instance
        dry_run: If True, don't save to database or send to Feishu
        test: If True, only crawl a small sample
    """
    logger.info("=== Starting News Crawling ===")

    # Load configurations
    keywords_config = load_config(PROJECT_ROOT / 'config' / 'keywords.json')
    sources_config = load_config(PROJECT_ROOT / 'config' / 'sources.json')

    # Initialize modules
    crawler = NewsCrawler()
    keyword_filter = KeywordFilter(keywords_config)
    deduplicator = Deduplicator(db_manager)

    try:
        # Get news sources
        news_sources = sources_config.get('news_sources', [])

        # Flatten all keywords for crawling
        all_keywords = []
        for category, kws in keywords_config.get('news', {}).items():
            all_keywords.extend(kws)

        # Crawl news
        logger.info(f"Crawling news from {len(news_sources)} sources...")
        news_items = crawler.crawl(news_sources, all_keywords[:10])  # Limit keywords
        logger.info(f"Crawled {len(news_items)} news items")

        if not news_items:
            logger.warning("No news items crawled")
            return

        # Filter by keywords
        filtered_news = keyword_filter.filter_news(news_items)
        logger.info(f"Filtered to {len(filtered_news)} news items")

        if not filtered_news:
            logger.warning("No news items passed keyword filter")
            return

        # Deduplicate
        unique_news = deduplicator.deduplicate_news(filtered_news)
        logger.info(f"After deduplication: {len(unique_news)} news items")

        if not unique_news:
            logger.info("No new news items to add")
            return

        if dry_run:
            logger.info("DRY RUN: Would save and send the following news:")
            for news in unique_news[:3]:
                logger.info(f"  - {news.title}")
            return

        # Save to database
        saved_count = 0
        for news in unique_news:
            news_id = db_manager.insert_news(news)
            if news_id:
                saved_count += 1

        logger.info(f"Saved {saved_count} new news items to database")

        # Send to Feishu (if not test mode)
        if not test:
            # Get unsent news and send top N
            unsent_news = db_manager.get_unsent_news(limit=NEWS_PER_WEEK)

            if unsent_news:
                # Send news
                success = feishu_bot.send_news_batch(unsent_news)

                if success:
                    # Mark as sent
                    news_ids = [news.id for news in unsent_news]
                    sent_date = datetime.now().isoformat()
                    db_manager.mark_news_sent(news_ids, sent_date)
                    logger.info(f"Sent {len(unsent_news)} news to Feishu")
                else:
                    logger.error("Failed to send news to Feishu")
            else:
                logger.info("No unsent news to send")

    except Exception as e:
        logger.error(f"Error in news crawling: {e}", exc_info=True)
        feishu_bot.send_error_notification(str(e), "News Crawling")
    finally:
        crawler.close()


def crawl_papers_and_patents(db_manager: DatabaseManager, feishu_bot: FeishuBot,
                             dry_run: bool = False, test: bool = False):
    """
    Crawl and process papers and patents

    Args:
        db_manager: Database manager
        feishu_bot: Feishu bot instance
        dry_run: If True, don't save to database or send to Feishu
        test: If True, only crawl a small sample
    """
    logger.info("=== Starting Papers & Patents Crawling ===")

    # Load configurations
    keywords_config = load_config(PROJECT_ROOT / 'config' / 'keywords.json')
    sources_config = load_config(PROJECT_ROOT / 'config' / 'sources.json')

    # Initialize modules
    paper_crawler = PaperCrawler()
    patent_crawler = PatentCrawler()
    keyword_filter = KeywordFilter(keywords_config)
    deduplicator = Deduplicator(db_manager)

    try:
        # Crawl papers
        paper_sources = sources_config.get('paper_sources', [])
        paper_keywords = keywords_config.get('papers', [])

        logger.info(f"Crawling papers from {len(paper_sources)} sources...")
        papers = paper_crawler.crawl(paper_sources, paper_keywords, max_results=30)
        logger.info(f"Crawled {len(papers)} papers")

        # Filter and deduplicate papers
        if papers:
            filtered_papers = keyword_filter.filter_papers(papers)
            unique_papers = deduplicator.deduplicate_papers(filtered_papers)
            logger.info(f"After filtering and deduplication: {len(unique_papers)} papers")

            if not dry_run:
                for paper in unique_papers:
                    db_manager.insert_paper(paper)
                logger.info(f"Saved {len(unique_papers)} papers to database")
        else:
            unique_papers = []

        # Crawl patents
        patent_sources = sources_config.get('patent_sources', [])
        patent_keywords = keywords_config.get('patents', [])

        logger.info(f"Crawling patents from {len(patent_sources)} sources...")
        patents = patent_crawler.crawl(patent_sources, patent_keywords)
        logger.info(f"Crawled {len(patents)} patents")

        # Filter and deduplicate patents
        if patents:
            filtered_patents = keyword_filter.filter_patents(patents)
            unique_patents = deduplicator.deduplicate_patents(filtered_patents)
            logger.info(f"After filtering and deduplication: {len(unique_patents)} patents")

            if not dry_run:
                for patent in unique_patents:
                    db_manager.insert_patent(patent)
                logger.info(f"Saved {len(unique_patents)} patents to database")
        else:
            unique_patents = []

        if dry_run:
            logger.info("DRY RUN: Would send papers and patents")
            return

        # Send to Feishu (if not test mode)
        if not test:
            unsent_papers = db_manager.get_unsent_papers(limit=PAPERS_PER_WEEK)
            unsent_patents = db_manager.get_unsent_patents(limit=PATENTS_PER_WEEK)

            if unsent_papers or unsent_patents:
                success = feishu_bot.send_papers_and_patents(unsent_papers, unsent_patents)

                if success:
                    sent_date = datetime.now().isoformat()
                    if unsent_papers:
                        paper_ids = [p.id for p in unsent_papers]
                        db_manager.mark_papers_sent(paper_ids, sent_date)
                    if unsent_patents:
                        patent_ids = [p.id for p in unsent_patents]
                        db_manager.mark_patents_sent(patent_ids, sent_date)

                    logger.info(f"Sent {len(unsent_papers)} papers and {len(unsent_patents)} patents to Feishu")
                else:
                    logger.error("Failed to send papers/patents to Feishu")
            else:
                logger.info("No unsent papers or patents to send")

    except Exception as e:
        logger.error(f"Error in papers/patents crawling: {e}", exc_info=True)
        feishu_bot.send_error_notification(str(e), "Papers & Patents Crawling")
    finally:
        paper_crawler.close()
        patent_crawler.close()


def update_website(db_manager: DatabaseManager):
    """
    Update static website

    Args:
        db_manager: Database manager
    """
    logger.info("=== Updating Website ===")

    try:
        generator = WebsiteGenerator(db_manager)
        generator.generate_all()
        generator.generate_readme()
        logger.info("Website updated successfully")

    except Exception as e:
        logger.error(f"Error updating website: {e}", exc_info=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Manufacturing Info Spider')
    parser.add_argument('--type', choices=['news', 'papers_patents', 'update_web', 'all'],
                       required=True, help='Type of task to run')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without saving or sending (for testing)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: crawl less data, don\'t send to Feishu')
    parser.add_argument('--test-feishu', action='store_true',
                       help='Test Feishu bot connection')
    parser.add_argument('--setup-scheduler', action='store_true',
                       help='Print scheduler setup instructions')

    args = parser.parse_args()

    # Print scheduler setup instructions
    if args.setup_scheduler:
        TaskScheduler.print_setup_instructions()
        return

    # Initialize database
    db_manager = DatabaseManager(DATABASE_PATH)
    logger.info(f"Database initialized at: {DATABASE_PATH}")

    # Initialize Feishu bot
    feishu_bot = FeishuBot()

    # Test Feishu connection
    if args.test_feishu:
        logger.info("Testing Feishu bot connection...")
        success = feishu_bot.send_text("🤖 Manufacturing Info Spider 测试消息")
        if success:
            logger.info("Feishu bot test successful!")
        else:
            logger.error("Feishu bot test failed!")
        return

    # Execute tasks based on type
    if args.type == 'news' or args.type == 'all':
        crawl_news(db_manager, feishu_bot, dry_run=args.dry_run, test=args.test)

    if args.type == 'papers_patents' or args.type == 'all':
        crawl_papers_and_patents(db_manager, feishu_bot, dry_run=args.dry_run, test=args.test)

    if args.type == 'update_web' or args.type == 'all':
        update_website(db_manager)

    logger.info("=== Task Completed ===")


if __name__ == '__main__':
    main()
