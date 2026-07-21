"""Demo module for testing Account class - Lab 2 Support File."""

from account import Account


def main() -> None:
    """Manual testing entrypoint."""
    custom_account = Account("Alice", 100.0)
    default_account = Account()

    print(custom_account)
    print(default_account)


if __name__ == "__main__":
    main()
