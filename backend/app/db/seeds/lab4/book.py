"""Book Class - Lab 4 Model Solution."""


class Book:
    """Represents a book with validated title, author, and read-only description properties."""

    def __init__(self, title: str, author: str) -> None:
        """Initialize book title and author using properties for validation."""
        self._title = ""
        self._author = ""
        self.title = title
        self.author = author

    def get_title(self) -> str:
        """Getter for title property."""
        return self._title

    def set_title(self, value: str) -> None:
        """Setter for title property with validation."""
        if not isinstance(value, str):
            raise TypeError("Title must be a string")
        if not value:
            raise ValueError("Title cannot be empty")
        self._title = value

    # Define title property using property() built-in function
    title = property(get_title, set_title)

    @property
    def author(self) -> str:
        """Getter for author property using @property decorator."""
        return self._author

    @author.setter
    def author(self, value: str) -> None:
        """Setter for author property with validation."""
        if not isinstance(value, str):
            raise TypeError("Author must be a string")
        if not value:
            raise ValueError("Author cannot be empty")
        self._author = value

    @property
    def description(self) -> str:
        """Read-only description property."""
        return f"{self._title} was written by {self._author}."

    def __str__(self) -> str:
        """Return string representation of book."""
        return f"{self._title} by {self._author}"


def main() -> None:
    """Main testing entrypoint."""
    my_book = Book("Harry Potter", "J.K. Rowling")
    print(my_book)
    print(my_book.description)


if __name__ == "__main__":
    main()
