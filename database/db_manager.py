"""
Database manager for manufacturing info spider
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from database.models import News, Patent, Paper

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager class"""

    def __init__(self, db_path: Path):
        """Initialize database manager"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _create_tables(self):
        """Create database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create news table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT,
                    publish_date TEXT,
                    summary TEXT,
                    content TEXT,
                    keywords TEXT,
                    score INTEGER DEFAULT 0,
                    is_sent BOOLEAN DEFAULT 0,
                    sent_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create patents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    application_no TEXT UNIQUE NOT NULL,
                    publication_no TEXT,
                    application_date TEXT,
                    publication_date TEXT,
                    applicant TEXT,
                    inventor TEXT,
                    abstract TEXT,
                    keywords TEXT,
                    is_sent BOOLEAN DEFAULT 0,
                    sent_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create papers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    title_cn TEXT,
                    authors TEXT,
                    abstract TEXT,
                    abstract_cn TEXT,
                    pdf_url TEXT,
                    arxiv_id TEXT UNIQUE,
                    publish_date TEXT,
                    keywords TEXT,
                    is_sent BOOLEAN DEFAULT 0,
                    sent_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_url ON news(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_is_sent ON news(is_sent)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patents_application_no ON patents(application_no)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patents_is_sent ON patents(is_sent)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_is_sent ON papers(is_sent)')

            logger.info("Database tables created successfully")

    def insert_news(self, news: News) -> Optional[int]:
        """Insert news article"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                data = news.to_dict()
                del data['id']

                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                sql = f'INSERT INTO news ({columns}) VALUES ({placeholders})'

                cursor.execute(sql, list(data.values()))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"News already exists: {news.url}")
            return None

    def insert_patent(self, patent: Patent) -> Optional[int]:
        """Insert patent"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                data = patent.to_dict()
                del data['id']

                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                sql = f'INSERT INTO patents ({columns}) VALUES ({placeholders})'

                cursor.execute(sql, list(data.values()))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Patent already exists: {patent.application_no}")
            return None

    def insert_paper(self, paper: Paper) -> Optional[int]:
        """Insert paper"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                data = paper.to_dict()
                del data['id']

                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                sql = f'INSERT INTO papers ({columns}) VALUES ({placeholders})'

                cursor.execute(sql, list(data.values()))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Paper already exists: {paper.arxiv_id}")
            return None

    def get_unsent_news(self, limit: int = None) -> List[News]:
        """Get unsent news articles"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = 'SELECT * FROM news WHERE is_sent = 0 ORDER BY created_at DESC'
            if limit:
                sql += f' LIMIT {limit}'
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [News.from_dict(dict(row)) for row in rows]

    def get_unsent_patents(self, limit: int = None) -> List[Patent]:
        """Get unsent patents"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = 'SELECT * FROM patents WHERE is_sent = 0 ORDER BY created_at DESC'
            if limit:
                sql += f' LIMIT {limit}'
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Patent.from_dict(dict(row)) for row in rows]

    def get_unsent_papers(self, limit: int = None) -> List[Paper]:
        """Get unsent papers"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = 'SELECT * FROM papers WHERE is_sent = 0 ORDER BY created_at DESC'
            if limit:
                sql += f' LIMIT {limit}'
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Paper.from_dict(dict(row)) for row in rows]

    def mark_news_sent(self, news_ids: List[int], sent_date: str):
        """Mark news as sent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in news_ids])
            cursor.execute(
                f'UPDATE news SET is_sent = 1, sent_date = ? WHERE id IN ({placeholders})',
                [sent_date] + news_ids
            )
            logger.info(f"Marked {len(news_ids)} news as sent")

    def mark_patents_sent(self, patent_ids: List[int], sent_date: str):
        """Mark patents as sent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in patent_ids])
            cursor.execute(
                f'UPDATE patents SET is_sent = 1, sent_date = ? WHERE id IN ({placeholders})',
                [sent_date] + patent_ids
            )
            logger.info(f"Marked {len(patent_ids)} patents as sent")

    def mark_papers_sent(self, paper_ids: List[int], sent_date: str):
        """Mark papers as sent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in paper_ids])
            cursor.execute(
                f'UPDATE papers SET is_sent = 1, sent_date = ? WHERE id IN ({placeholders})',
                [sent_date] + paper_ids
            )
            logger.info(f"Marked {len(paper_ids)} papers as sent")

    def get_all_news(self, limit: int = 100) -> List[News]:
        """Get all news articles"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM news ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [News.from_dict(dict(row)) for row in rows]

    def get_all_patents(self, limit: int = 100) -> List[Patent]:
        """Get all patents"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM patents ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [Patent.from_dict(dict(row)) for row in rows]

    def get_all_papers(self, limit: int = 100) -> List[Paper]:
        """Get all papers"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM papers ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [Paper.from_dict(dict(row)) for row in rows]

    def url_exists(self, url: str) -> bool:
        """Check if URL exists in news table"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM news WHERE url = ?', (url,))
            return cursor.fetchone() is not None

    def patent_exists(self, application_no: str) -> bool:
        """Check if patent exists"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM patents WHERE application_no = ?', (application_no,))
            return cursor.fetchone() is not None

    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if paper exists"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM papers WHERE arxiv_id = ?', (arxiv_id,))
            return cursor.fetchone() is not None
