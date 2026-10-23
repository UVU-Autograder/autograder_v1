"""Module 4 Lab 2: Even or Odd Checker with Loop and Exit Option."""

# Loop continuously until user chooses to quit
while True:
    option = input("Enter option (\"c\" to check, \"q\" to quit): ").strip().lower()

    if option == "q":
        print("Program terminated.")
        break
    elif option == "c":
        number = int(input("Enter a number: "))
        if number % 2 == 0:
            print(f"The number {number} is even.")
        else:
            print(f"The number {number} is odd.")
