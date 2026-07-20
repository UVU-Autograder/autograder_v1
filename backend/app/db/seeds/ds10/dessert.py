"""Dessert Shop class hierarchy for DS10."""

from abc import ABC, abstractmethod
from typing import Any
from packaging import Packaging
from payment import Payable, PayType
from combine import Combinable

VALID_PAY_TYPES = ("CASH", "CARD", "PHONE")


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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DessertItem):
            return self.calculate_cost() == other.calculate_cost()
        return False

    def __ne__(self, other: Any) -> bool:
        return not (self == other)

    def __lt__(self, other: "DessertItem") -> bool:
        if isinstance(other, DessertItem):
            return self.calculate_cost() < other.calculate_cost()
        return NotImplemented

    def __gt__(self, other: "DessertItem") -> bool:
        if isinstance(other, DessertItem):
            return self.calculate_cost() > other.calculate_cost()
        return NotImplemented

    def __le__(self, other: "DessertItem") -> bool:
        if isinstance(other, DessertItem):
            return self.calculate_cost() <= other.calculate_cost()
        return NotImplemented

    def __ge__(self, other: "DessertItem") -> bool:
        if isinstance(other, DessertItem):
            return self.calculate_cost() >= other.calculate_cost()
        return NotImplemented


class Candy(DessertItem):
    """Candy dessert item (structurally Combinable)."""

    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0) -> None:
        super().__init__(name, "Bag")
        self.candy_weight = candy_weight
        self.price_per_pound = price_per_pound

    def calculate_cost(self) -> float:
        return round(self.candy_weight * self.price_per_pound, 2)

    def can_combine(self, other: Combinable) -> bool:
        if isinstance(other, Candy):
            return self.name == other.name and self.price_per_pound == other.price_per_pound
        return False

    def combine(self, other: Combinable) -> "Candy":
        if self.can_combine(other) and isinstance(other, Candy):
            self.candy_weight += other.candy_weight
        return self

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.packaging})\n"
            f"  {self.candy_weight:.2f} lbs. @ ${self.price_per_pound:.2f}/lb: ${self.calculate_cost():.2f} [Tax: ${self.calculate_tax():.2f}]"
        )


class Cookie(DessertItem):
    """Cookie dessert item (structurally Combinable)."""

    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0) -> None:
        super().__init__(name, "Box")
        self.cookie_quantity = cookie_quantity
        self.price_per_dozen = price_per_dozen

    def calculate_cost(self) -> float:
        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)

    def can_combine(self, other: Combinable) -> bool:
        if isinstance(other, Cookie):
            return self.name == other.name and self.price_per_dozen == other.price_per_dozen
        return False

    def combine(self, other: Combinable) -> "Cookie":
        if self.can_combine(other) and isinstance(other, Cookie):
            self.cookie_quantity += other.cookie_quantity
        return self

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


class Order(Payable):
    """Order container holding items."""

    def __init__(self) -> None:
        self.order: list[DessertItem] = []
        self._pay_type: PayType = "CASH"

    def add(self, item: DessertItem) -> None:
        if isinstance(item, Combinable):
            for existing in self.order:
                if isinstance(existing, Combinable) and existing.can_combine(item):
                    existing.combine(item)
                    return
        self.order.append(item)

    def __len__(self) -> int:
        return len(self.order)

    def get_pay_type(self) -> PayType:
        return self._pay_type

    def set_pay_type(self, payment_method: PayType) -> None:
        if payment_method not in VALID_PAY_TYPES:
            raise ValueError(f"Invalid payment method: {payment_method}")
        self._pay_type = payment_method

    def sort(self) -> None:
        self.order.sort()

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
        lines.append(f"Payment Method: {self._pay_type}")
        return "\n".join(lines)
