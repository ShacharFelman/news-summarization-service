"""Data schemas for the fetchers app."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class ArticleData:
    """Schema for standardized article format."""
    title: str
    url: str
    published_at: datetime
    source_name: str
    content: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
