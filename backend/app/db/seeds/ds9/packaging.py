"""Packaging Protocol definition for Dessert Shop."""

from typing import Protocol


class Packaging(Protocol):
    """Protocol for items that define a packaging string attribute."""

    packaging: str
