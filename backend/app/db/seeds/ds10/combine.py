"""Combinable Protocol definition for Dessert Shop."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Combinable(Protocol):
    """Protocol for items that support merging/combining like items."""

    def can_combine(self, other: "Combinable") -> bool: ...
    def combine(self, other: "Combinable") -> "Combinable": ...
