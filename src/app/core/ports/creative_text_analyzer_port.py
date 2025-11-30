"""Creative Text Analyzer Port.

Interface for marketing creative text analysis operations.
"""

from typing import Protocol

from ..domain.entities import CreativeTextAnalysisResult


class CreativeTextAnalyzerPort(Protocol):
    """Port interface for creative text analysis.

    Defines the contract for analyzing marketing creative text,
    extracting quality scores, marketing tags, and sentiment.

    Usage:
        This port supports the IA Marketing V1 feature (Sprint 9),
        enabling AI-powered analysis of ad creative text to extract
        actionable marketing insights.

    Implementations:
        - V1: Pure Python heuristic-based analyzer (no external dependencies)
        - Future: LLM-based analyzer (e.g., Claude, GPT)
    """

    def analyze_text(self, text: str) -> CreativeTextAnalysisResult:
        """Analyze marketing creative text.

        Performs comprehensive analysis of the input text to extract:
        - Quality score (0-100) based on marketing best practices
        - Style tags (e.g., "minimalist", "bold", "storytelling")
        - Angle tags (e.g., "urgency", "social-proof", "benefit-driven")
        - Tone tags (e.g., "casual", "professional", "emotional")
        - Sentiment (positive, neutral, negative)

        This method is intentionally synchronous as the V1 implementation
        uses pure Python heuristics without I/O operations.

        Args:
            text: The creative text to analyze (title, body, caption combined).

        Returns:
            CreativeTextAnalysisResult containing all extracted metrics.

        Note:
            - Empty or whitespace-only text will return a minimal score
            - Very short text (< 10 chars) may result in limited tag extraction
            - The method should never raise exceptions - invalid input
              should return a valid result with low scores
        """
        ...
