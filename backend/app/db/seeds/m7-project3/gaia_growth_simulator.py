"""Project 3: Population Growth Simulator - Gaia Viability Estimator."""

import sys


def compute_next_population(current_pop: float, rate: float) -> float:
    """Compute next step's population using the logistic equation: P_n = r * P_(n-1) * (1 - P_(n-1))."""
    return rate * current_pop * (1.0 - current_pop)


def validate_inputs(p0: float, rate: float, steps: int) -> bool:
    """Validate that simulation parameters are within allowable ranges."""
    if not (0.0 < p0 < 1.0):
        print(f"Error: Initial population ({p0}) must be between 0 and 1.")
        return False
    if not (0.0 < rate < 4.0):
        print(f"Error: Growth rate ({rate}) must be between 0 and 4.")
        return False
    if steps <= 0:
        print(f"Error: Number of steps ({steps}) must be a positive integer.")
        return False
    return True


def simulate_population(p0: float, rate: float, steps: int) -> list[float]:
    """Simulate population growth across given number of steps using accumulator list."""
    history = [p0]
    curr = p0
    for _ in range(steps):
        curr = compute_next_population(curr, rate)
        history.append(curr)
    return history


def write_results(history: list[float], filename: str) -> None:
    """Write simulation history to specified output file formatted to 3 decimal places."""
    with open(filename, "w", encoding="utf-8") as f:
        for step, pop in enumerate(history):
            f.write(f"{step}   {pop:.3f}\n")


def main() -> None:
    if len(sys.argv) < 5:
        print("Usage: python gaia_growth_simulator.py <p0> <r> <steps> <output_filename>")
        sys.exit(1)

    try:
        p0 = float(sys.argv[1])
        rate = float(sys.argv[2])
        steps = int(sys.argv[3])
        output_filename = sys.argv[4]
    except ValueError as exc:
        print(f"Invalid argument types: {exc}")
        sys.exit(1)

    if not validate_inputs(p0, rate, steps):
        sys.exit(1)

    history = simulate_population(p0, rate, steps)
    write_results(history, output_filename)


if __name__ == "__main__":
    main()
