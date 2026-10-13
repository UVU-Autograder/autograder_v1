"""Strategy registry for resolving language runners and outcome parsers."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.grading.protocols import LanguageStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry maintaining active language execution strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, LanguageStrategy] = {}

    def register(self, language: str, strategy: LanguageStrategy) -> None:
        """Register a strategy for a given language identifier."""
        key = language.strip().lower()
        self._strategies[key] = strategy
        logger.debug("Registered grading strategy for language '%s'", key)

    def get(self, language: str | None = None) -> LanguageStrategy:
        """Retrieve strategy for language, defaulting to 'python'."""
        key = (language or "python").strip().lower()
        if key not in self._strategies:
            available = ", ".join(sorted(self._strategies.keys()))
            raise ValueError(
                f"Unsupported language '{language}'. Available strategies: [{available}]"
            )
        return self._strategies[key]

    def has(self, language: str) -> bool:
        """Return True if strategy exists for language."""
        return language.strip().lower() in self._strategies

    def list_languages(self) -> list[str]:
        """List registered language identifiers."""
        return sorted(self._strategies.keys())


# Global singleton instance
registry = StrategyRegistry()


def get_strategy(language: str | None = None) -> LanguageStrategy:
    """Convenience getter for global strategy resolution."""
    return registry.get(language)


def register_strategy(language: str, strategy: LanguageStrategy) -> None:
    """Convenience registration for custom language strategies."""
    registry.register(language, strategy)
