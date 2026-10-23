"""Module 5 Lab 2: Input Validation for Name and Age Using try/except."""


def get_valid_name() -> str:
    """Prompt until a non-empty, non-numeric name is provided."""
    while True:
        name = input("Enter your name: ").strip()
        # Name must be non-empty and not purely numeric
        if name and not name.isnumeric():
            return name
        print("Invalid name. Please enter a non-numeric name.")


def get_valid_age() -> int:
    """Prompt until a valid integer age is entered using try/except."""
    while True:
        age_str = input("Enter your age: ").strip()
        try:
            age = int(age_str)
            return age
        except ValueError:
            print("Invalid age. Please enter an integer.")


def main() -> None:
    # Collect validated user inputs
    name = get_valid_name()
    age = get_valid_age()
    print(f"Thanks, {name}! Your age is {age}.")


if __name__ == "__main__":
    main()
