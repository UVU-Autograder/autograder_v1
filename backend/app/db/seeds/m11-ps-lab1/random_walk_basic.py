"""Simulate Random Grid Movement (Lance's Pattern).

Simulates a single astronaut's 100-step walk on a 2D grid, tracking
positions as coordinate tuples and plotting the trajectory.
"""

import random

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def simulate_walk(steps=100):
    """Simulate random 2D grid movement for the specified number of steps."""
    # Possible directions: Up, Down, Left, Right
    directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]

    # Starting position at the origin
    current_x, current_y = 0, 0
    positions = [(current_x, current_y)]

    # Loop for 100 steps updating coordinates
    for _ in range(steps):
        dx, dy = random.choice(directions)
        current_x += dx
        current_y += dy
        positions.append((current_x, current_y))

    return positions


def plot_walk(positions):
    """Plot the trajectory taken during the random walk."""
    if plt is None:
        return

    # Extract x and y coordinates
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]

    plt.figure(figsize=(8, 8))
    plt.plot(xs, ys, marker="o", color="blue", label="Path")
    plt.scatter([xs[0]], [ys[0]], color="green", s=120, label="Start (0,0)")
    plt.scatter([xs[-1]], [ys[-1]], color="red", s=120, label="End")
    plt.title("Lance's Random Walk Simulation (100 steps)")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)
    plt.legend()
    plt.savefig("random_walk.png")
    plt.close()


def main():
    # Simulate walk of 100 steps
    positions = simulate_walk(100)
    final_x, final_y = positions[-1]

    # Print final position
    print(f"Final position after 100 steps: ({final_x}, {final_y})")

    # Plot the walk
    plot_walk(positions)


if __name__ == "__main__":
    main()
