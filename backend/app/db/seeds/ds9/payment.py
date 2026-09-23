"""Payment method Protocol definition for Dessert Shop."""

from typing import Literal, Protocol, runtime_checkable

PayType = Literal["CASH", "CARD", "PHONE"]


@runtime_checkable
class Payable(Protocol):
    """Protocol for objects that manage payment method types."""

    def get_pay_type(self) -> PayType: ...
    def set_pay_type(self, payment_method: PayType) -> None: ...
