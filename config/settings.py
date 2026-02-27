"""
Global settings for manufacturing info spider
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
WEB_OUTPUT_DIR = OUTPUT_DIR / "website"

# Database settings
DATABASE_PATH = DATA_DIR / "crawler.db"

# Feishu settings
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
FEISHU_SECRET = os.getenv("FEISHU_SECRET", "")

# Crawler settings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY_MIN = 1  # seconds
REQUEST_DELAY_MAX = 3  # seconds
MAX_RETRIES = 3

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = PROJECT_ROOT / "spider.log"

# Push settings
NEWS_PER_WEEK = 3
PAPERS_PER_WEEK = 4
PATENTS_PER_WEEK = 5

# Website settings
SITE_TITLE = "制造业信息资讯"
SITE_DESCRIPTION = "智能制造、机器人、AI技术相关新闻、专利、论文汇总"
GITHUB_REPO = ""  # Set this to your GitHub repo URL
GITHUB_PAGES_URL = ""  # Set this to your GitHub Pages URL

# Schedule settings (for reference, actual scheduling done via Windows Task Scheduler)
NEWS_SCHEDULE = {
    "days": ["MON", "WED", "FRI"],
    "time": "10:00"
}

PAPERS_PATENTS_SCHEDULE = {
    "days": ["FRI"],
    "time": "14:00"
}

WEB_UPDATE_SCHEDULE = {
    "days": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
    "time": "22:00"
}
