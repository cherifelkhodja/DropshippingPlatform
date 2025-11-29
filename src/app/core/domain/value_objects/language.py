"""Language Value Object.

Represents a validated ISO 639-1 language code.
"""

from dataclasses import dataclass

from ..errors import InvalidLanguageError


# ISO 639-1 language codes (most common ones)
VALID_LANGUAGE_CODES: frozenset[str] = frozenset(
    {
        "en",  # English
        "fr",  # French
        "de",  # German
        "es",  # Spanish
        "it",  # Italian
        "pt",  # Portuguese
        "nl",  # Dutch
        "pl",  # Polish
        "ru",  # Russian
        "ja",  # Japanese
        "zh",  # Chinese
        "ko",  # Korean
        "ar",  # Arabic
        "hi",  # Hindi
        "tr",  # Turkish
        "vi",  # Vietnamese
        "th",  # Thai
        "id",  # Indonesian
        "ms",  # Malay
        "sv",  # Swedish
        "no",  # Norwegian
        "da",  # Danish
        "fi",  # Finnish
        "el",  # Greek
        "cs",  # Czech
        "ro",  # Romanian
        "hu",  # Hungarian
        "uk",  # Ukrainian
        "he",  # Hebrew
        "bn",  # Bengali
    }
)


@dataclass(frozen=True)
class Language:
    """Immutable language value object with ISO 639-1 validation.

    Attributes:
        code: The two-letter language code (lowercase).
    """

    code: str

    def __post_init__(self) -> None:
        """Validate language code after initialization."""
        # Normalize to lowercase for comparison
        normalized = self.code.lower() if self.code else ""

        if not normalized:
            raise InvalidLanguageError(self.code)

        if len(normalized) != 2:
            raise InvalidLanguageError(self.code)

        if normalized not in VALID_LANGUAGE_CODES:
            raise InvalidLanguageError(self.code)

        # Use object.__setattr__ since dataclass is frozen
        object.__setattr__(self, "code", normalized)

    def __str__(self) -> str:
        return self.code

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Language):
            return self.code == other.code
        return False

    def __hash__(self) -> int:
        return hash(self.code)
