"""Dessert Shop class hierarchy for DS7."""

from abc import ABC, abstractmethod
from typing import Any
from packaging import Packaging


class DessertItem(ABC, Packaging):
    """Abstract base class for all dessert items."""

    def __init__(self, name: str = "", packaging: str | None = None) -> None:
        self.name = name
        self.packaging = packaging
        self.tax_percent: float = 7.25

    @abstractmethod
    def calculate_cost(self) -> float:
        pass

    def calculate_tax(self) -> float:
        return round(self.calculate_cost() * (self.tax_percent / 100), 2)


class Candy(DessertItem):
    """Candy dessert item."""

    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0) -> None:
        super().__init__(name, "Bag")
        self.candy_weight = candy_weight
        self.price_per_pound = price_per_pound

    def calculate_cost(self) -> float:
        return round(self.candy_weight * self.price_per_pound, 2)

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.packaging})\n"
            f"  {self.candy_weight:.2f} lbs. @ ${self.price_per_pound:.2f}/lb: ${self.calculate_cost():.2f} [Tax: ${self.calculate_tax():.2f}]"
        )


class Cookie(DessertItem):
    """Cookie dessert item."""

    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0) -> None:
        super().__init__(name, "Box")
        self.cookie_quantity = cookie_quantity
        self.price_per_dozen = price_per_dozen

    def calculate_cost(self) -> float:
        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.packaging})\n"
            f"  {self.cookie_quantity} cookies @ ${self.price_per_dozen:.2f}/dz: ${self.calculate_cost():.2f} [Tax: ${self.calculate_tax():.2f}]"
        )


class IceCream(DessertItem):
    """IceCream dessert item."""

    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0) -> None:
        super().__init__(name, "Bowl")
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop

    def calculate_cost(self) -> float:
        return round(self.scoop_count * self.price_per_scoop, 2)

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.packaging})\n"
            f"  {self.scoop_count} scoops @ ${self.price_per_scoop:.2f}/scoop: ${self.calculate_cost():.2f} [Tax: ${self.calculate_tax():.2f}]"
        )


class Sundae(IceCream):
    """Sundae dessert item."""

    def __init__(
        self,
        name: str = "",
        scoop_count: int = 0,
        price_per_scoop: float = 0.0,
        topping_name: str = "",
        topping_price: float = 0.0,
    ) -> None:
        super().__init__(name, scoop_count, price_per_scoop)
        self.packaging = "Boat"
        self.topping_name = topping_name
        self.topping_price = topping_price

    def calculate_cost(self) -> float:
        return round((self.scoop_count * self.price_per_scoop) + self.topping_price, 2)

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.packaging})\n"
            f"  {self.scoop_count} scoops @ ${self.price_per_scoop:.2f}/scoop + {self.topping_name} @ ${self.topping_price:.2f}: ${self.calculate_cost():.2f} [Tax: ${self.calculate_tax():.2f}]"
        )


class Order:
    """Order container holding items."""

    def __init__(self) -> None:
        self.order: list[DessertItem] = []

    def add(self, item: DessertItem) -> None:
        self.order.append(item)

    def __len__(self) -> int:
        return len(self.order)

    def order_cost(self) -> float:
        return round(sum(item.calculate_cost() for item in self.order), 2)

    def order_tax(self) -> float:
        return round(sum(item.calculate_tax() for item in self.order), 2)

    def total_cost(self) -> float:
        return round(self.order_cost() + self.order_tax(), 2)

    def to_list(self) -> list[list[Any]]:
        return [
            [
                item.name,
                item.packaging,
                f"${item.calculate_cost():.2f}",
                f"${item.calculate_tax():.2f}",
            ]
            for item in self.order
        ]

    def __str__(self) -> str:
        lines = ["Order:"]
        for item in self.order:
            lines.append(str(item))
        lines.append(f"Subtotal: ${self.order_cost():.2f}")
        lines.append(f"Tax: ${self.order_tax():.2f}")
        lines.append(f"Total: ${self.total_cost():.2f}")
        return "\n".join(lines)
