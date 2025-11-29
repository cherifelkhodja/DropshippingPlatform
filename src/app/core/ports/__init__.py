"""Ports for the Dropshipping Platform.

Ports define the interfaces (contracts) that adapters must implement.
They follow the hexagonal architecture pattern, separating domain logic
from infrastructure concerns.

Ports are defined using typing.Protocol for structural subtyping.
"""

from .meta_ads_port import MetaAdsPort
from .html_scraper_port import HtmlScraperPort
from .sitemap_port import SitemapPort
from .repository_port import (
    PageRepository,
    AdsRepository,
    ScanRepository,
    KeywordRunRepository,
    ScoringRepository,
    WatchlistRepository,
)
from .task_dispatcher_port import TaskDispatcherPort
from .logging_port import LoggingPort

__all__ = [
    # Meta Ads
    "MetaAdsPort",
    # Scraping
    "HtmlScraperPort",
    "SitemapPort",
    # Repositories
    "PageRepository",
    "AdsRepository",
    "ScanRepository",
    "KeywordRunRepository",
    "ScoringRepository",
    "WatchlistRepository",
    # Task Orchestration
    "TaskDispatcherPort",
    # Logging
    "LoggingPort",
]
