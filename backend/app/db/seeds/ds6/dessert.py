from abc import ABC, abstractmethod


class DessertItem(ABC):
    def __init__(self, name: str = ""):
        self.name = name
        self.tax_percent: float = 7.25

    @abstractmethod
    def calculate_cost(self) -> float:
        pass

    def calculate_tax(self) -> float:
        return round(self.calculate_cost() * (self.tax_percent / 100), 2)


class Candy(DessertItem):
    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
        super().__init__(name)
        self.candy_weight = candy_weight
        self.price_per_pound = price_per_pound

    def calculate_cost(self) -> float:
        return round(self.candy_weight * self.price_per_pound, 2)

    def __str__(self) -> str:
        return (
            f"{self.name}\n"
            f"-    {self.candy_weight} lbs. @ ${self.price_per_pound}/lb:, "
            f"${self.calculate_cost():.2f}, [Tax: ${self.calculate_tax():.2f}]"
        )


class Cookie(DessertItem):
    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0):
        super().__init__(name)
        self.cookie_quantity = cookie_quantity
        self.price_per_dozen = price_per_dozen

    def calculate_cost(self) -> float:
        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)

    def __str__(self) -> str:
        return (
            f"{self.name} Cookies\n"
            f"-    {self.cookie_quantity} cookies. @ ${self.price_per_dozen}/dozen:, "
            f"${self.calculate_cost():.2f}, [Tax: ${self.calculate_tax():.2f}]"
        )


class IceCream(DessertItem):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
        super().__init__(name)
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop

    def calculate_cost(self) -> float:
        return round(self.scoop_count * self.price_per_scoop, 2)

    def __str__(self) -> str:
        return (
            f"{self.name} Ice Cream\n"
            f"-    {self.scoop_count} scoops. @ ${self.price_per_scoop}/scoop:, "
            f"${self.calculate_cost():.2f}, [Tax: ${self.calculate_tax():.2f}]"
        )


class Sundae(IceCream):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
        super().__init__(name, scoop_count, price_per_scoop)
        self.topping_name = topping_name
        self.topping_price = topping_price

    def calculate_cost(self) -> float:
        base_cost = super().calculate_cost()
        return round(base_cost + self.topping_price, 2)

    def __str__(self) -> str:
        return (
            f"{self.topping_name} {self.name} Sundae\n"
            f"-    {self.scoop_count} scoops. @ ${self.price_per_scoop}/scoop\n"
            f"-    {self.topping_name} topping @ ${self.topping_price}:, "
            f"${self.calculate_cost():.2f}, [Tax: ${self.calculate_tax():.2f}]"
        )


class Order:
    def __init__(self) -> None:
        self.order: list[DessertItem] = []
        self._index: int = 0

    def add(self, item: DessertItem) -> None:
        self.order.append(item)

    def __len__(self) -> int:
        return len(self.order)

    def __iter__(self) -> "Order":
        self._index = 0
        return self

    def __next__(self) -> DessertItem:
        if self._index >= len(self.order):
            raise StopIteration
        item = self.order[self._index]
        self._index += 1
        return item

    def order_cost(self) -> float:
        return round(sum(item.calculate_cost() for item in self.order), 2)

    def order_tax(self) -> float:
        return round(sum(item.calculate_tax() for item in self.order), 2)

    def __str__(self) -> str:
        return "\n".join(str(item) for item in self.order)

    def to_list(self) -> list[list[str]]:
        rows = []
        for item in self.order:
            lines = str(item).split("\n")
            rows.append([
                lines[0],
                f"${item.calculate_cost():.2f}",
                f"[Tax: ${item.calculate_tax():.2f}]"
            ])
            for detail in lines[1:]:
                rows.append([detail, "", ""])

        rows.append(["----------", "----------", "----------"])
        rows.append([
            "Total number of items in order:",
            str(len(self)),
            ""
        ])
        rows.append([
            "Order Subtotals:",
            f"${self.order_cost():.2f}",
            f"[Tax: ${self.order_tax():.2f}]"
        ])
        rows.append([
            "Order Total:",
            "",
            f"${self.order_cost() + self.order_tax():.2f}"
        ])
        return rows
