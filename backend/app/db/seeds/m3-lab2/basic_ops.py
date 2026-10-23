"""Module 3 Lab 2: Basic Arithmetic Function (Add / Sub/ Multi/ Div)."""


def calculate_operations(num1: float, num2: float) -> None:
    """Compute and print addition, subtraction, multiplication, and division for two numbers."""
    addition = num1 + num2
    subtraction = num1 - num2
    multiplication = num1 * num2
    division = num1 / num2 if num2 != 0 else 0

    print(f"For inputs {num1:.0f} and {num2:.0f}:")
    print(f"Addition: {addition:.0f}")
    print(f"Subtraction: {subtraction:.0f}")
    print(f"Multiplication: {multiplication:.0f}")
    print(f"Division: {division:.1f}")


def main() -> None:
    # Prompt user for inputs
    first = float(input("Enter the first number: "))
    second = float(input("Enter the second number: "))
    # Accept operation prompt
    _ = input("Enter operation (+, -, *, /, all): ")

    calculate_operations(first, second)


if __name__ == "__main__":
    main()
