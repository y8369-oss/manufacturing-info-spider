"""
Database models for manufacturing info spider
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class News:
    """News article model"""
    id: Optional[int] = None
    title: str = ""
    url: str = ""
    source: str = ""
    publish_date: Optional[str] = None
    summary: str = ""
    content: str = ""
    keywords: List[str] = None
    score: int = 0
    is_sent: bool = False
    sent_date: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'publish_date': self.publish_date,
            'summary': self.summary,
            'content': self.content,
            'keywords': json.dumps(self.keywords, ensure_ascii=False),
            'score': self.score,
            'is_sent': self.is_sent,
            'sent_date': self.sent_date,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        if isinstance(data.get('keywords'), str):
            data['keywords'] = json.loads(data['keywords'])
        return cls(**data)


@dataclass
class Patent:
    """Patent model"""
    id: Optional[int] = None
    title: str = ""
    application_no: str = ""
    publication_no: str = ""
    application_date: Optional[str] = None
    publication_date: Optional[str] = None
    applicant: str = ""
    inventor: str = ""
    abstract: str = ""
    keywords: List[str] = None
    is_sent: bool = False
    sent_date: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'application_no': self.application_no,
            'publication_no': self.publication_no,
            'application_date': self.application_date,
            'publication_date': self.publication_date,
            'applicant': self.applicant,
            'inventor': self.inventor,
            'abstract': self.abstract,
            'keywords': json.dumps(self.keywords, ensure_ascii=False),
            'is_sent': self.is_sent,
            'sent_date': self.sent_date,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        if isinstance(data.get('keywords'), str):
            data['keywords'] = json.loads(data['keywords'])
        return cls(**data)


@dataclass
class Paper:
    """Academic paper model"""
    id: Optional[int] = None
    title: str = ""
    title_cn: str = ""
    authors: str = ""
    abstract: str = ""
    abstract_cn: str = ""
    pdf_url: str = ""
    arxiv_id: str = ""
    publish_date: Optional[str] = None
    keywords: List[str] = None
    is_sent: bool = False
    sent_date: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'title_cn': self.title_cn,
            'authors': self.authors,
            'abstract': self.abstract,
            'abstract_cn': self.abstract_cn,
            'pdf_url': self.pdf_url,
            'arxiv_id': self.arxiv_id,
            'publish_date': self.publish_date,
            'keywords': json.dumps(self.keywords, ensure_ascii=False),
            'is_sent': self.is_sent,
            'sent_date': self.sent_date,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        if isinstance(data.get('keywords'), str):
            data['keywords'] = json.loads(data['keywords'])
        return cls(**data)
