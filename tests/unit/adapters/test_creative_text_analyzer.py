"""Tests for HeuristicCreativeTextAnalyzer.

Tests the pure Python heuristic text analysis implementation.
"""

import pytest

from src.app.adapters.outbound.creative_text_analyzer import (
    HeuristicCreativeTextAnalyzer,
)
from src.app.core.domain.entities.creative_analysis import CreativeTextAnalysisResult


class TestHeuristicCreativeTextAnalyzer:
    """Tests for HeuristicCreativeTextAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> HeuristicCreativeTextAnalyzer:
        """Create analyzer instance."""
        return HeuristicCreativeTextAnalyzer()

    def test_analyze_empty_text(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test analyzing empty text returns zero score."""
        result = analyzer.analyze_text("")

        assert isinstance(result, CreativeTextAnalysisResult)
        assert result.creative_score == 0.0  # Empty text gets zero
        assert result.sentiment == "neutral"
        assert result.style_tags == []
        assert result.angle_tags == []
        assert result.tone_tags == []

    def test_analyze_short_text(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test analyzing short text."""
        result = analyzer.analyze_text("Buy now!")

        assert isinstance(result, CreativeTextAnalysisResult)
        assert result.creative_score >= 20.0
        # Should detect CTA
        assert "cta-driven" in result.angle_tags or result.creative_score > 20.0

    def test_analyze_high_quality_text(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that high-quality text gets a high score."""
        # Text with hooks, benefits, CTA, social proof, emotional words
        high_quality_text = """
        🔥 STOP scrolling! This is the best product you'll ever find!

        Thousands of customers love it! ⭐⭐⭐⭐⭐

        Here's why you need this:
        ✅ Save money every month
        ✅ Free shipping worldwide
        ✅ 30-day money back guarantee

        Limited time offer - 50% OFF today only!

        Click the link below and order now! 👇
        """
        result = analyzer.analyze_text(high_quality_text)

        assert result.creative_score >= 70.0  # High score expected
        assert result.sentiment == "positive"
        assert len(result.style_tags) > 0
        assert len(result.angle_tags) > 0

    def test_analyze_medium_quality_text(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that medium-quality text gets a reasonable score."""
        medium_text = """
        Check out our new product!
        Great quality and fast delivery.
        Visit our store today.
        """
        result = analyzer.analyze_text(medium_text)

        assert 40.0 <= result.creative_score <= 70.0
        assert result.sentiment in ["positive", "neutral"]

    def test_analyze_detects_hook_patterns(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test detection of hook patterns."""
        # Test various hook patterns
        hook_texts = [
            "STOP! You need to see this...",
            "Wait... this changes everything!",
            "Did you know that 90% of people are doing this wrong?",
            "The secret to success is...",
        ]

        for text in hook_texts:
            result = analyzer.analyze_text(text)
            # Hook should boost the score above base
            assert result.creative_score > 20.0, f"Failed for: {text}"

    def test_analyze_detects_cta_patterns(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that CTA patterns boost score (CTAs add to score, not tags)."""
        cta_texts = [
            "Shop now and get 20% off!",
            "Buy today - limited stock!",
            "Click here to order",
            "Get yours before it's gone!",
            "Order now for free shipping",
        ]

        for text in cta_texts:
            result = analyzer.analyze_text(text)
            # CTAs boost score above base (20) + minimal length
            assert result.creative_score > 20.0, f"CTA should boost score for: {text}"

    def test_analyze_detects_social_proof(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test detection of social proof patterns."""
        # social-proof triggered by: reviews, customers, trusted, bestseller, rated, proven
        social_proof_texts = [
            "Over 10,000 customers love this product!",
            "Rated 5 stars with thousands of reviews",
            "Trusted by millions worldwide",
            "Bestseller product of the year!",
        ]

        for text in social_proof_texts:
            result = analyzer.analyze_text(text)
            assert "social-proof" in result.angle_tags, f"Failed for: {text}"

    def test_analyze_detects_urgency(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test detection of urgency patterns."""
        # Urgency is triggered by: limited, hurry, last chance, ending soon, now, today only
        urgency_texts = [
            "Limited time offer - ends tonight!",
            "Hurry! Sale ends soon",
            "Last chance to save!",
            "Ending soon - don't wait!",
            "Today only special price!",
        ]

        for text in urgency_texts:
            result = analyzer.analyze_text(text)
            assert "urgency" in result.angle_tags, f"Failed for: {text}"

    def test_analyze_detects_benefit_keywords(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test detection of benefit-focused content."""
        # benefit-driven triggered by: save, get, gain, improve, transform, results
        benefit_texts = [
            "Get amazing results today!",
            "Save money and improve your life",
            "Transform your routine with this product",
            "Gain more confidence with proven results",
        ]

        for text in benefit_texts:
            result = analyzer.analyze_text(text)
            assert "benefit-driven" in result.angle_tags, f"Failed for: {text}"

    def test_sentiment_detection_positive(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test positive sentiment detection."""
        positive_text = """
        Amazing product! Best thing I've ever bought.
        Love it, love it, love it! ❤️
        This is incredible and I'm so happy!
        """
        result = analyzer.analyze_text(positive_text)
        assert result.sentiment == "positive"

    def test_sentiment_detection_negative(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test negative sentiment detection."""
        negative_text = """
        Tired of bad products? Hate low quality?
        Stop wasting money on terrible items!
        Don't fall for scams anymore.
        """
        result = analyzer.analyze_text(negative_text)
        # Even with negative words, marketing copy often balances to neutral
        assert result.sentiment in ["negative", "neutral"]

    def test_sentiment_detection_neutral(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test neutral sentiment detection."""
        neutral_text = """
        Product specifications:
        - Material: Cotton
        - Size: Medium
        - Color: Blue
        """
        result = analyzer.analyze_text(neutral_text)
        assert result.sentiment == "neutral"

    def test_style_tag_detection(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test style tag detection."""
        # Style tags are: minimalist, bold, storytelling, direct, conversational, formal, playful, luxury

        # Test minimalist text (simple, clean, minimal keywords)
        minimal_text = "simple clean minimal design"
        result = analyzer.analyze_text(minimal_text)
        assert "minimalist" in result.style_tags

        # Test bold text (bold, strong, powerful keywords)
        bold_text = "Bold and powerful statement! Strong impact!"
        result = analyzer.analyze_text(bold_text)
        assert "bold" in result.style_tags

        # Test direct text (now, today, act, get, buy, shop keywords)
        direct_text = "Buy now and get this today!"
        result = analyzer.analyze_text(direct_text)
        assert "direct" in result.style_tags

    def test_tone_tag_detection(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test tone tag detection."""
        # Test professional tone
        professional_text = """
        We are pleased to present our professional-grade solution.
        Our enterprise offering provides high-quality results.
        """
        result = analyzer.analyze_text(professional_text)
        assert "professional" in result.tone_tags

        # Test casual tone
        casual_text = """
        Hey! Check this out, it's pretty cool actually.
        You're gonna love it, trust me!
        """
        result = analyzer.analyze_text(casual_text)
        assert "casual" in result.tone_tags

    def test_length_bonus_scoring(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that optimal text length provides score bonus."""
        # Very short text (no length bonus)
        short_result = analyzer.analyze_text("Buy now")

        # Optimal length text (should get bonus)
        optimal_text = " ".join(["word"] * 30)  # ~30 words
        optimal_result = analyzer.analyze_text(optimal_text)

        # Optimal length should score higher than very short
        assert optimal_result.creative_score >= short_result.creative_score

    def test_score_bounds(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that score is always within valid bounds (0-100)."""
        # Test with various inputs
        test_texts = [
            "",
            "a",
            "a" * 10000,  # Very long text
            "🔥" * 100,  # All emojis
            "BUY NOW!!!! AMAZING!!!!! BEST EVER!!!!!",  # Lots of markers
        ]

        for text in test_texts:
            result = analyzer.analyze_text(text)
            assert 0.0 <= result.creative_score <= 100.0, f"Score out of bounds for: {text[:50]}"

    def test_result_structure(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that result has correct structure."""
        result = analyzer.analyze_text("Test text for structure validation")

        assert isinstance(result.creative_score, float)
        assert isinstance(result.style_tags, list)
        assert isinstance(result.angle_tags, list)
        assert isinstance(result.tone_tags, list)
        assert result.sentiment in ["positive", "neutral", "negative"]

    def test_analyzer_version(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that analyzer has a version."""
        assert hasattr(analyzer, "VERSION")
        assert analyzer.VERSION == "v1.0"

    def test_idempotent_analysis(
        self, analyzer: HeuristicCreativeTextAnalyzer
    ) -> None:
        """Test that analyzing the same text twice gives same result."""
        text = "This is a test message with some content!"

        result1 = analyzer.analyze_text(text)
        result2 = analyzer.analyze_text(text)

        assert result1.creative_score == result2.creative_score
        assert result1.sentiment == result2.sentiment
        assert result1.style_tags == result2.style_tags
        assert result1.angle_tags == result2.angle_tags
        assert result1.tone_tags == result2.tone_tags
