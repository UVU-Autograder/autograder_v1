"""Weighted Movement and Frequency Counter (Sophie's Pattern).

CS 1400 - Module 12 PS Lab 1
Simulates 200 steps of biased movement on a 2D grid:
- 50% chance to move Up
- 16.67% chance to move Down
- 16.67% chance to move Left
- 16.67% chance to move Right
Tracks position and counts frequency of each direction.
"""

import random


def simulate_sophie_walk(steps=200):
    """Simulate biased 2D grid movement for 200 steps using weighted random choices."""
    directions = ["Up", "Down", "Left", "Right"]
    # 50% chance for Up, 16.67% each for Down, Left, and Right
    weights = [0.50, 0.1667, 0.1667, 0.1667]
    movements = {
        "Up": (0, 1),
        "Down": (0, -1),
        "Left": (-1, 0),
        "Right": (1, 0),
    }

    counts = {"Up": 0, "Down": 0, "Left": 0, "Right": 0}
    current_x, current_y = 0, 0

    # Simulate 200 steps of movement
    for _ in range(steps):
        chosen_direction = random.choices(directions, weights=weights, k=1)[0]
        counts[chosen_direction] += 1

        dx, dy = movements[chosen_direction]
        current_x += dx
        current_y += dy

    return (current_x, current_y), counts


def main():
    # Run the 200-step simulation
    final_pos, counts = simulate_sophie_walk(200)

    # Display final position and statistics
    print(f"Final position: {final_pos}")
    print("Direction counts:")
    print(f"Up: {counts['Up']}")
    print(f"Down: {counts['Down']}")
    print(f"Left: {counts['Left']}")
    print(f"Right: {counts['Right']}")


if __name__ == "__main__":
    main()
