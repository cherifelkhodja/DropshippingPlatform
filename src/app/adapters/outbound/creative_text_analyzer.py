"""Creative Text Analyzer V1 - Pure Python Heuristic Implementation.

This adapter implements the CreativeTextAnalyzerPort using pure Python
heuristics (regex, keyword sets) without external API calls.

Scoring Algorithm (0-100):
- Base score: 20 points
- Length bonus: up to 15 points (optimal 100-300 chars)
- Hook presence: 15 points (questions, "you", "imagine", etc.)
- Benefit keywords: 15 points (results, save, get, etc.)
- CTA presence: 15 points (buy now, shop now, etc.)
- Social proof: 10 points (reviews, testimonials, numbers)
- Emotional words: 10 points (amazing, incredible, etc.)

Tags are extracted based on keyword/pattern detection.
Sentiment is determined via positive/negative lexicon analysis.
"""

import re
from typing import cast

from src.app.core.domain.entities.creative_analysis import (
    CreativeTextAnalysisResult,
    SentimentType,
)


# =============================================================================
# KEYWORD SETS FOR ANALYSIS
# =============================================================================

# Hook indicators - words/patterns that grab attention
HOOK_PATTERNS = [
    r"\?",  # Questions
    r"^(imagine|picture|think|what if|did you know)",
    r"\b(you|your|you're|you'll)\b",
    r"\b(stop|wait|attention|warning|alert)\b",
    r"\b(secret|hidden|exclusive|limited)\b",
]

# Benefit keywords - words indicating value/results
BENEFIT_KEYWORDS = {
    "save", "free", "bonus", "gift", "win", "earn", "get",
    "results", "success", "transform", "improve", "boost",
    "guaranteed", "proven", "effective", "works", "solution",
    "easy", "simple", "fast", "quick", "instant",
    "discount", "offer", "deal", "sale", "off",
}

# CTA (Call-to-Action) patterns
CTA_PATTERNS = [
    r"\b(buy\s+now|shop\s+now|order\s+now|get\s+yours)\b",
    r"\b(click\s+here|learn\s+more|find\s+out|discover)\b",
    r"\b(sign\s+up|subscribe|join\s+now|register)\b",
    r"\b(try\s+it|start\s+now|begin\s+today|act\s+now)\b",
    r"\b(claim|grab|unlock|access)\b",
    r"\b(add\s+to\s+cart|checkout|get\s+started)\b",
    # French CTAs
    r"\b(achetez|commandez|profitez|découvrez)\b",
    r"\b(cliquez\s+ici|en\s+savoir\s+plus)\b",
]

# Social proof indicators
SOCIAL_PROOF_PATTERNS = [
    r"\b\d+[+]?\s*(reviews?|avis|customers?|clients?|users?)\b",
    r"\b\d+[%]?\s*(satisfaction|happy|satisfied)\b",
    r"\b(bestseller|best\s+seller|top\s+rated|#1|number\s+one)\b",
    r"\b(trusted|verified|certified|approved)\b",
    r"\b(testimonial|review|rating|stars?)\b",
    r"\b(million|thousand|[0-9]+k\+?)\s*(sold|customers?|users?)\b",
]

# Emotional/power words
EMOTIONAL_WORDS = {
    "amazing", "incredible", "unbelievable", "stunning", "breathtaking",
    "revolutionary", "groundbreaking", "life-changing", "game-changer",
    "love", "perfect", "beautiful", "gorgeous", "fantastic", "wonderful",
    "exciting", "thrilling", "mind-blowing", "epic", "awesome",
    "urgent", "now", "today", "limited", "exclusive", "rare",
    "finally", "breakthrough", "secret", "powerful", "ultimate",
}

# Positive sentiment words
POSITIVE_WORDS = {
    "love", "great", "amazing", "wonderful", "excellent", "fantastic",
    "perfect", "best", "happy", "beautiful", "awesome", "incredible",
    "brilliant", "outstanding", "superb", "delighted", "thrilled",
    "enjoy", "recommend", "favorite", "blessed", "grateful", "joy",
    "success", "win", "achieve", "accomplish", "proud", "excited",
}

# Negative sentiment words
NEGATIVE_WORDS = {
    "hate", "terrible", "awful", "horrible", "worst", "bad", "poor",
    "disappointed", "frustrating", "annoying", "useless", "waste",
    "problem", "issue", "fail", "broken", "wrong", "error",
    "angry", "upset", "sad", "worried", "stressed", "anxious",
    "scam", "fake", "fraud", "misleading", "overpriced",
}

# Style tag keywords
STYLE_TAGS_MAP = {
    "minimalist": ["simple", "clean", "minimal", "less is more"],
    "bold": ["bold", "strong", "powerful", "intense", "striking"],
    "storytelling": ["story", "journey", "discover", "imagine", "once upon"],
    "direct": ["now", "today", "act", "get", "buy", "shop"],
    "conversational": ["you", "your", "we", "us", "let's", "hey", "hi"],
    "formal": ["please", "kindly", "hereby", "therefore", "regarding"],
    "playful": ["fun", "enjoy", "love", "wow", "yay", "awesome"],
    "luxury": ["premium", "exclusive", "luxury", "elite", "vip", "first-class"],
}

# Angle tag keywords
ANGLE_TAGS_MAP = {
    "urgency": ["limited", "hurry", "last chance", "ending soon", "now", "today only"],
    "social-proof": ["reviews", "customers", "trusted", "bestseller", "rated", "proven"],
    "benefit-driven": ["save", "get", "gain", "improve", "transform", "results"],
    "problem-solution": ["problem", "solution", "fix", "solve", "struggle", "finally"],
    "fear-of-missing-out": ["miss", "don't miss", "exclusive", "limited", "only", "left"],
    "value-proposition": ["free", "bonus", "discount", "deal", "offer", "save"],
    "curiosity": ["secret", "discover", "find out", "learn", "revealed", "hidden"],
    "authority": ["expert", "professional", "certified", "approved", "doctor", "scientist"],
}

# Tone tag keywords
TONE_TAGS_MAP = {
    "casual": ["hey", "hi", "cool", "awesome", "gonna", "wanna", "super"],
    "professional": ["professional", "enterprise", "solution", "expertise", "industry"],
    "emotional": ["love", "heart", "feel", "passion", "dream", "believe"],
    "informative": ["learn", "discover", "understand", "know", "fact", "information"],
    "humorous": ["lol", "haha", "funny", "joke", "laugh", "hilarious"],
    "inspirational": ["dream", "believe", "achieve", "inspire", "motivation", "success"],
    "aggressive": ["now", "act", "hurry", "don't wait", "limited", "final"],
}


class HeuristicCreativeTextAnalyzer:
    """V1 Creative Text Analyzer using pure Python heuristics.

    This implementation analyzes marketing creative text without
    external API dependencies, using regex patterns and keyword
    matching to extract quality scores, tags, and sentiment.

    The scoring algorithm is documented at the top of this module.
    """

    VERSION = "v1.0"

    def analyze_text(self, text: str) -> CreativeTextAnalysisResult:
        """Analyze marketing creative text.

        Args:
            text: The creative text to analyze.

        Returns:
            CreativeTextAnalysisResult with score, tags, and sentiment.
        """
        # Handle empty/whitespace text
        if not text or not text.strip():
            return CreativeTextAnalysisResult(
                creative_score=0.0,
                style_tags=[],
                angle_tags=[],
                tone_tags=[],
                sentiment="neutral",
            )

        # Normalize text for analysis
        text_lower = text.lower().strip()
        text_len = len(text)

        # Calculate component scores
        base_score = 20.0
        length_score = self._score_length(text_len)
        hook_score = self._score_hooks(text_lower)
        benefit_score = self._score_benefits(text_lower)
        cta_score = self._score_ctas(text_lower)
        social_proof_score = self._score_social_proof(text_lower)
        emotional_score = self._score_emotional(text_lower)

        # Calculate total score (clamped to 0-100)
        total_score = min(100.0, max(0.0,
            base_score +
            length_score +
            hook_score +
            benefit_score +
            cta_score +
            social_proof_score +
            emotional_score
        ))

        # Extract tags
        style_tags = self._extract_tags(text_lower, STYLE_TAGS_MAP)
        angle_tags = self._extract_tags(text_lower, ANGLE_TAGS_MAP)
        tone_tags = self._extract_tags(text_lower, TONE_TAGS_MAP)

        # Determine sentiment
        sentiment = self._analyze_sentiment(text_lower)

        return CreativeTextAnalysisResult(
            creative_score=round(total_score, 1),
            style_tags=style_tags,
            angle_tags=angle_tags,
            tone_tags=tone_tags,
            sentiment=sentiment,
        )

    def _score_length(self, length: int) -> float:
        """Score based on text length (optimal: 100-300 chars).

        Args:
            length: Number of characters in text.

        Returns:
            Score between 0 and 15.
        """
        if length < 10:
            return 0.0
        elif length < 50:
            return 5.0
        elif length < 100:
            return 10.0
        elif length <= 300:
            return 15.0  # Optimal range
        elif length <= 500:
            return 12.0
        elif length <= 800:
            return 8.0
        else:
            return 5.0  # Too long

    def _score_hooks(self, text: str) -> float:
        """Score based on hook/attention-grabbing elements.

        Args:
            text: Lowercased text to analyze.

        Returns:
            Score between 0 and 15.
        """
        hook_count = 0
        for pattern in HOOK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                hook_count += 1

        if hook_count == 0:
            return 0.0
        elif hook_count == 1:
            return 8.0
        elif hook_count == 2:
            return 12.0
        else:
            return 15.0

    def _score_benefits(self, text: str) -> float:
        """Score based on benefit/value keywords.

        Args:
            text: Lowercased text to analyze.

        Returns:
            Score between 0 and 15.
        """
        benefit_count = sum(1 for word in BENEFIT_KEYWORDS if word in text)

        if benefit_count == 0:
            return 0.0
        elif benefit_count == 1:
            return 5.0
        elif benefit_count <= 3:
            return 10.0
        else:
            return 15.0

    def _score_ctas(self, text: str) -> float:
        """Score based on call-to-action presence.

        Args:
            text: Lowercased text to analyze.

        Returns:
            Score between 0 and 15.
        """
        cta_count = 0
        for pattern in CTA_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                cta_count += 1

        if cta_count == 0:
            return 0.0
        elif cta_count == 1:
            return 10.0
        else:
            return 15.0  # Multiple CTAs

    def _score_social_proof(self, text: str) -> float:
        """Score based on social proof elements.

        Args:
            text: Lowercased text to analyze.

        Returns:
            Score between 0 and 10.
        """
        proof_count = 0
        for pattern in SOCIAL_PROOF_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                proof_count += 1

        if proof_count == 0:
            return 0.0
        elif proof_count == 1:
            return 6.0
        else:
            return 10.0

    def _score_emotional(self, text: str) -> float:
        """Score based on emotional/power words.

        Args:
            text: Lowercased text to analyze.

        Returns:
            Score between 0 and 10.
        """
        emotional_count = sum(1 for word in EMOTIONAL_WORDS if word in text)

        if emotional_count == 0:
            return 0.0
        elif emotional_count == 1:
            return 4.0
        elif emotional_count <= 3:
            return 7.0
        else:
            return 10.0

    def _extract_tags(
        self,
        text: str,
        tag_map: dict[str, list[str]],
    ) -> list[str]:
        """Extract tags based on keyword presence.

        Args:
            text: Lowercased text to analyze.
            tag_map: Dictionary mapping tag names to keyword lists.

        Returns:
            List of detected tag names.
        """
        detected_tags: list[str] = []

        for tag, keywords in tag_map.items():
            for keyword in keywords:
                if keyword in text:
                    detected_tags.append(tag)
                    break  # Only add tag once

        return detected_tags

    def _analyze_sentiment(self, text: str) -> SentimentType:
        """Analyze overall sentiment of text.

        Uses simple lexicon-based approach counting positive
        vs negative words.

        Args:
            text: Lowercased text to analyze.

        Returns:
            Sentiment type: positive, neutral, or negative.
        """
        words = set(re.findall(r'\b\w+\b', text))

        positive_count = len(words & POSITIVE_WORDS)
        negative_count = len(words & NEGATIVE_WORDS)

        # Calculate sentiment ratio
        total = positive_count + negative_count
        if total == 0:
            return "neutral"

        ratio = positive_count / total

        if ratio >= 0.7:
            return "positive"
        elif ratio <= 0.3:
            return "negative"
        else:
            return "neutral"
