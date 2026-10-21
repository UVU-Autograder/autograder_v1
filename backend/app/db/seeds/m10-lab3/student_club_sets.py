"""Module 10 Lab 3: Student Club Memberships Using Sets."""


def main() -> None:
    # Initialize club membership sets
    coding_club = {"Alice", "Bob", "Charlie", "Dana"}
    robotics_club = {"Charlie", "Eve", "Frank", "Bob"}

    # Intersection: students in both clubs
    both = coding_club & robotics_club
    print(f"Students in both clubs: {both}")

    # Symmetric difference: students in only one club
    only_one = coding_club ^ robotics_club
    print(f"Students in only one club: {only_one}")

    # Difference: students only in coding club
    only_coding = coding_club - robotics_club
    print(f"Students only in the coding club: {only_coding}")

    # Add Grace to coding club
    coding_club.add("Grace")

    # Remove Eve from robotics club safely
    robotics_club.discard("Eve")

    # Union: all unique students
    all_unique = coding_club | robotics_club
    print(f"All unique students: {all_unique}")


if __name__ == "__main__":
    main()
