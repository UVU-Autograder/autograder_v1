"""Module 9 Lab 2: Student Scorebook with Dictionary."""


def main() -> None:
    # Initialize empty dictionary
    scorebook = {}

    # Populate initial student scores
    scorebook["Alice"] = 88
    scorebook["Bob"] = 75
    scorebook["Charlie"] = 93
    scorebook["Dana"] = 80

    # Print all names and scores using for loop and .items()
    for name, score in scorebook.items():
        print(f"{name}: {score}")
    print()

    # Update Dana's score
    scorebook["Dana"] = 85
    print("Updated Dana's score to 85")

    # Delete Bob using .pop()
    scorebook.pop("Bob", None)
    print("Removed Bob from the scorebook")

    # Check for Eve using .get()
    if scorebook.get("Eve") is None:
        print("Eve not found in scorebook.")
    else:
        print(f"Eve's score is {scorebook.get('Eve')}")

    # Calculate and print average score of remaining students
    remaining_scores = list(scorebook.values())
    avg = sum(remaining_scores) / len(remaining_scores)
    print(f"Average score: {avg:.2f}")


if __name__ == "__main__":
    main()
