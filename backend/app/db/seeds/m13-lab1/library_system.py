"""Build a Simple Library Using Objects.

CS 1400 - Module 13 Lab 1
Models library books using Object-Oriented Programming principles:
constructors, string representation, instance methods, and object collections.
"""


class Book:
    """Represents a book in the library system."""

    def __init__(self, title, author, year, available=True):
        """Initialize book attributes."""
        self.title = title
        self.author = author
        self.year = year
        self.available = available

    def borrow(self):
        """Mark the book as borrowed and display confirmation."""
        self.available = False
        print(f"Book borrowed: {self.title}")

    def return_book(self):
        """Mark the book as returned and display confirmation."""
        self.available = True
        print(f"Book returned: {self.title}")

    def is_available(self):
        """Return True if book is available, False otherwise."""
        return self.available

    def __str__(self):
        """Return readable string representation of the book."""
        status = "[Available]" if self.available else "[Checked Out]"
        return f"'{self.title}' by {self.author} ({self.year}) {status}"


def main():
    # Create 3 Book objects
    book1 = Book("Clean Code", "Robert Martin", 2008)
    book2 = Book("Atomic Habits", "James Clear", 2018)
    book3 = Book("Deep Work", "Cal Newport", 2016)

    # Store books in a list
    library = [book1, book2, book3]

    # Borrow one book and return it
    book1.borrow()
    book1.return_book()

    print("\nLibrary Collection:")
    # Use a loop to display all books
    for book in library:
        print(book)


if __name__ == "__main__":
    main()
