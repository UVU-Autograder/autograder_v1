"""Module 6 Problem Solving Lab 1: Track Bacteria Growth Over Time."""


def main() -> None:
    # Gather simulation parameters from user
    start_pop = float(input("Enter starting population: ").strip())
    growth_rate = float(input("Enter hourly growth rate: ").strip())
    hours = int(input("Enter number of hours: ").strip())

    # Initialize history list with initial population at hour 0
    population_history = [round(start_pop, 2)]

    # Calculate and store population for each subsequent hour
    current_pop = start_pop
    for _ in range(hours):
        current_pop = round(current_pop * growth_rate, 2)
        population_history.append(current_pop)

    # Print population history for each hour
    for hour, pop in enumerate(population_history):
        print(f"Hour {hour}: {pop:.2f}")


if __name__ == "__main__":
    main()
