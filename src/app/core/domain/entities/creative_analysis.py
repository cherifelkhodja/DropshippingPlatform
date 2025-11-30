"""Creative Analysis Entity and Value Objects.

Domain entities for AI-powered marketing creative analysis.
Provides scoring, tagging, and sentiment analysis for ad creatives.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Optional


class Sentiment(Enum):
    """Enumeration of sentiment levels for creative text."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# Type alias for sentiment literal (for Pydantic compatibility)
SentimentType = Literal["positive", "neutral", "negative"]


@dataclass(frozen=True)
class CreativeTextAnalysisResult:
    """Value object representing the result of text analysis.

    This is the output of the CreativeTextAnalyzerPort and contains
    all extracted metrics from analyzing creative text.

    Attributes:
        creative_score: Quality score (0-100) based on marketing best practices.
        style_tags: Tags describing the creative style (e.g., "minimalist", "bold").
        angle_tags: Tags describing the marketing angle (e.g., "urgency", "social-proof").
        tone_tags: Tags describing the tone (e.g., "casual", "professional").
        sentiment: Overall sentiment of the creative.
    """

    creative_score: float
    style_tags: list[str] = field(default_factory=list)
    angle_tags: list[str] = field(default_factory=list)
    tone_tags: list[str] = field(default_factory=list)
    sentiment: SentimentType = "neutral"

    def __post_init__(self) -> None:
        """Validate score is within bounds."""
        if not 0.0 <= self.creative_score <= 100.0:
            raise ValueError(
                f"creative_score must be between 0 and 100, got {self.creative_score}"
            )


@dataclass(frozen=True)
class CreativeAnalysis:
    """Entity representing a persisted creative analysis.

    This entity stores the results of analyzing an ad's creative text,
    including quality score, marketing tags, and sentiment.

    Attributes:
        id: Unique identifier for this analysis record.
        ad_id: The ad this analysis belongs to.
        creative_score: Quality score (0-100).
        style_tags: Tags describing the creative style.
        angle_tags: Tags describing the marketing angle.
        tone_tags: Tags describing the tone.
        sentiment: Overall sentiment of the creative.
        analysis_version: Version of the analyzer used.
        created_at: When this analysis was performed.
    """

    id: str
    ad_id: str
    creative_score: float
    style_tags: list[str] = field(default_factory=list)
    angle_tags: list[str] = field(default_factory=list)
    tone_tags: list[str] = field(default_factory=list)
    sentiment: SentimentType = "neutral"
    analysis_version: str = "v1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate and normalize score after initialization."""
        # Clamp score to 0-100 range
        clamped_score = max(0.0, min(100.0, self.creative_score))
        object.__setattr__(self, "creative_score", clamped_score)

    @classmethod
    def create(
        cls,
        id: str,
        ad_id: str,
        analysis_result: CreativeTextAnalysisResult,
        analysis_version: str = "v1.0",
    ) -> "CreativeAnalysis":
        """Factory method to create a new CreativeAnalysis from analysis result.

        Args:
            id: Unique identifier for the analysis.
            ad_id: The ad this analysis belongs to.
            analysis_result: The result from the text analyzer.
            analysis_version: Version of the analyzer used.

        Returns:
            A new CreativeAnalysis instance.
        """
        return cls(
            id=id,
            ad_id=ad_id,
            creative_score=analysis_result.creative_score,
            style_tags=list(analysis_result.style_tags),
            angle_tags=list(analysis_result.angle_tags),
            tone_tags=list(analysis_result.tone_tags),
            sentiment=analysis_result.sentiment,
            analysis_version=analysis_version,
            created_at=datetime.utcnow(),
        )

    @property
    def all_tags(self) -> list[str]:
        """Get all tags combined (style + angle + tone)."""
        return self.style_tags + self.angle_tags + self.tone_tags

    @property
    def tags_count(self) -> int:
        """Get total number of tags."""
        return len(self.all_tags)

    def is_high_quality(self, threshold: float = 70.0) -> bool:
        """Check if this analysis indicates a high-quality creative.

        Args:
            threshold: The minimum score to be considered high quality.

        Returns:
            True if score meets or exceeds the threshold.
        """
        return self.creative_score >= threshold

    def is_low_quality(self, threshold: float = 30.0) -> bool:
        """Check if this analysis indicates a low-quality creative.

        Args:
            threshold: The maximum score to be considered low quality.

        Returns:
            True if score is below the threshold.
        """
        return self.creative_score < threshold

    def is_positive_sentiment(self) -> bool:
        """Check if the creative has positive sentiment."""
        return self.sentiment == "positive"

    def has_tag(self, tag: str) -> bool:
        """Check if the analysis has a specific tag.

        Args:
            tag: The tag to search for (case-insensitive).

        Returns:
            True if the tag is present in any tag category.
        """
        tag_lower = tag.lower()
        return any(t.lower() == tag_lower for t in self.all_tags)

    def get_quality_tier(self) -> str:
        """Get a quality tier based on creative score.

        Returns:
            Quality tier: "excellent", "good", "average", or "poor".
        """
        if self.creative_score >= 80:
            return "excellent"
        elif self.creative_score >= 60:
            return "good"
        elif self.creative_score >= 40:
            return "average"
        else:
            return "poor"

    def __eq__(self, other: object) -> bool:
        """Check equality based on identity (id)."""
        if isinstance(other, CreativeAnalysis):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<CreativeAnalysis(id={self.id}, ad_id={self.ad_id}, "
            f"score={self.creative_score:.1f}, sentiment={self.sentiment})>"
        )


@dataclass(frozen=True)
class PageCreativeInsights:
    """Read-model for aggregated creative insights for a page.

    Provides summary statistics and top creatives for a page's
    advertising creative analysis.

    Attributes:
        page_id: The page identifier.
        avg_score: Average creative score across all analyzed ads.
        best_score: Highest creative score among analyzed ads.
        top_creatives: List of top-scoring creative analyses.
        total_analyzed: Total number of creatives analyzed.
        computed_at: When insights were computed.
    """

    page_id: str
    avg_score: float = 0.0
    best_score: float = 0.0
    top_creatives: list[CreativeAnalysis] = field(default_factory=list)
    total_analyzed: int = 0
    computed_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_analyses(
        cls,
        page_id: str,
        analyses: list[CreativeAnalysis],
        top_n: int = 5,
    ) -> "PageCreativeInsights":
        """Factory method to create insights from a list of analyses.

        Args:
            page_id: The page identifier.
            analyses: List of creative analyses for the page.
            top_n: Number of top creatives to include (default 5).

        Returns:
            A new PageCreativeInsights instance.
        """
        if not analyses:
            return cls(
                page_id=page_id,
                avg_score=0.0,
                best_score=0.0,
                top_creatives=[],
                total_analyzed=0,
                computed_at=datetime.utcnow(),
            )

        scores = [a.creative_score for a in analyses]
        avg_score = sum(scores) / len(scores)
        best_score = max(scores)

        # Sort by score descending and take top N
        sorted_analyses = sorted(
            analyses,
            key=lambda a: a.creative_score,
            reverse=True,
        )
        top_creatives = sorted_analyses[:top_n]

        return cls(
            page_id=page_id,
            avg_score=avg_score,
            best_score=best_score,
            top_creatives=top_creatives,
            total_analyzed=len(analyses),
            computed_at=datetime.utcnow(),
        )

    @property
    def has_high_quality_creatives(self) -> bool:
        """Check if there are any high-quality creatives (score >= 70)."""
        return self.best_score >= 70.0

    @property
    def quality_tier(self) -> str:
        """Get overall quality tier based on average score.

        Returns:
            Quality tier: "excellent", "good", "average", or "poor".
        """
        if self.avg_score >= 80:
            return "excellent"
        elif self.avg_score >= 60:
            return "good"
        elif self.avg_score >= 40:
            return "average"
        else:
            return "poor"

    @property
    def sentiment_distribution(self) -> dict[str, int]:
        """Get distribution of sentiments among top creatives.

        Returns:
            Dictionary with sentiment counts.
        """
        distribution: dict[str, int] = {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
        }
        for creative in self.top_creatives:
            distribution[creative.sentiment] += 1
        return distribution

    def get_creatives_by_sentiment(
        self, sentiment: SentimentType
    ) -> list[CreativeAnalysis]:
        """Get creatives filtered by sentiment.

        Args:
            sentiment: The sentiment to filter by.

        Returns:
            List of creatives with the specified sentiment.
        """
        return [c for c in self.top_creatives if c.sentiment == sentiment]

    def get_common_tags(self, min_count: int = 2) -> list[str]:
        """Get tags that appear in multiple top creatives.

        Args:
            min_count: Minimum occurrences to be considered common.

        Returns:
            List of common tags.
        """
        tag_counts: dict[str, int] = {}
        for creative in self.top_creatives:
            for tag in creative.all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return [tag for tag, count in tag_counts.items() if count >= min_count]

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<PageCreativeInsights(page_id={self.page_id}, "
            f"avg={self.avg_score:.1f}, best={self.best_score:.1f}, "
            f"total={self.total_analyzed})>"
        )
