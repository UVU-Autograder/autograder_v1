"""Module 8 Lab 2: Tuple-Based Number Guessing Game."""

import random


def main() -> None:
    # Generate tuple of 5 random integers between 1 and 20
    target_numbers = tuple(random.randint(1, 20) for _ in range(5))

    best_match_count = 0
    won = False

    for attempt in range(1, 6):
        prompt = f"Attempt {attempt}: Enter 5 numbers: "
        user_input = input(prompt).strip()
        try:
            guess = tuple(int(x) for x in user_input.split())
        except ValueError:
            print("Invalid input. Please enter 5 integers separated by spaces.")
            continue

        if len(guess) != 5:
            print("Please enter exactly 5 numbers.")
            continue

        if guess == target_numbers:
            print("You guessed correctly!")
            won = True
            break

        # Count how many match in the exact position
        matches = sum(1 for g, t in zip(guess, target_numbers) if g == t)
        if matches > best_match_count:
            best_match_count = matches

        print(f"{matches} numbers matched in the correct position.")

    if not won:
        best_pct = (best_match_count / 5) * 100
        print(f"Sorry! The correct combination was: {target_numbers}")
        print(f"Your best match was {best_pct:.0f}%.")


if __name__ == "__main__":
    main()
