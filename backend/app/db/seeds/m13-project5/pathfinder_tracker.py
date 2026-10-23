"""Pathfinder Tracker - Space Walk Simulation.

CS 1400 - Module 13 Project 5 (100 points)
Simulates spacewalk trajectories for three astronauts (Lance, Sophie, Finn)
aboard the Exodus generation ship using Object-Oriented Programming and
distinct directional movement patterns.
"""

import random

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


class Astronaut:
    """Represents an astronaut performing a spacewalk."""

    def __init__(self, name, color, marker):
        """Initialize astronaut name, visualization styling, and starting position."""
        self.name = name
        self.color = color
        self.marker = marker
        self.positions = [(0, 0)]

    @property
    def current_position(self):
        """Return the most recent (x, y) coordinate."""
        return self.positions[-1]

    def move(self, dx, dy):
        """Update current position and append new coordinate to positions list."""
        curr_x, curr_y = self.current_position
        new_pos = (curr_x + dx, curr_y + dy)
        self.positions.append(new_pos)

    def to_dict(self):
        """Return dictionary format expected by plot_pathfinder_walk."""
        return {
            "name": self.name,
            "positions": self.positions,
            "color": self.color,
            "marker": self.marker,
        }

    def __str__(self):
        """Return readable summary of astronaut spacewalk."""
        return (
            f"Astronaut {self.name}: Current Position = {self.current_position}, "
            f"Total Positions = {len(self.positions)}"
        )


def plot_pathfinder_walk(astronaut):
    """Plot a single astronaut's spacewalk path and save as <name>_spacewalk.png."""
    if plt is None:
        return

    # Unpack the list of positions into x and y sequences
    xs, ys = zip(*astronaut["positions"])

    plt.figure(figsize=(10, 10))

    # Plot the points and the connecting path
    plt.scatter(
        xs,
        ys,
        color=astronaut["color"],
        edgecolor="k",
        alpha=0.7,
        s=100,
        marker=astronaut["marker"],
    )
    plt.plot(xs, ys, lw=1.5, ls="--", color=astronaut["color"])

    plt.grid(True)
    plt.title(f'Pathfinder Spacewalk for {astronaut["name"]}')
    plt.xlabel("East-West")
    plt.ylabel("North-South")

    # Save to the required filename format, e.g. Lance_spacewalk.png
    plt.savefig(f'{astronaut["name"]}_spacewalk.png', dpi=300)
    plt.close()


def get_step_for_lance():
    """Lance moves randomly in any direction (Up, Down, Left, Right) with equal probability."""
    directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
    return random.choice(directions)


def get_step_for_sophie():
    """Sophie has a 50% chance of Up, and 16.67% each for Down, Left, Right."""
    directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
    weights = [0.50, 0.1667, 0.1667, 0.1667]
    return random.choices(directions, weights=weights, k=1)[0]


def get_step_for_finn():
    """Finn moves only horizontally (Left or Right) with equal probability."""
    directions = [(-1, 0), (1, 0)]
    return random.choice(directions)


def simulate_spacewalk(astronaut, steps=500):
    """Simulate the specified number of spacewalk steps for an astronaut."""
    step_generators = {
        "Lance": get_step_for_lance,
        "Sophie": get_step_for_sophie,
        "Finn": get_step_for_finn,
    }

    generator = step_generators.get(astronaut.name, get_step_for_lance)
    for _ in range(steps):
        dx, dy = generator()
        astronaut.move(dx, dy)


def main():
    # Initialize three astronauts
    lance = Astronaut("Lance", "b", "o")
    sophie = Astronaut("Sophie", "r", "s")
    finn = Astronaut("Finn", "g", "^")

    astronauts = [lance, sophie, finn]

    # Simulate 500 steps and plot each spacewalk
    for astronaut in astronauts:
        simulate_spacewalk(astronaut, steps=500)
        print(astronaut)
        plot_pathfinder_walk(astronaut.to_dict())


if __name__ == "__main__":
    main()
