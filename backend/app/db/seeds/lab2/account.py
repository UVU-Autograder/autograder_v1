"""Bank Account Class - Lab 2 Model Solution."""


class Account:
    """Represents a bank account with owner name and balance."""

    def __init__(self, owner: str = "", balance: float = 0.0) -> None:
        """Initialize account owner and balance."""
        self.owner = owner
        self.balance = float(balance)

    def __str__(self) -> str:
        """Return formatted string representation of account."""
        return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
