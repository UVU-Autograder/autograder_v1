from dessert import Candy, Cookie, IceCream, Order, Sundae
from tabulate import tabulate


class DessertShop:
    def user_prompt_candy(self) -> Candy:
        name = input("Enter the candy name: ")
        if not name.strip():
            raise ValueError("Name cannot be empty.")

        while True:
            try:
                weight = float(input("Enter candy weight(lbs): "))
                if weight <= 0:
                    print("Weight must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")

        while True:
            try:
                price = float(input("Enter the price per pound: "))
                if price <= 0:
                    print("Price must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")

        return Candy(name, weight, price)

    def user_prompt_cookie(self) -> Cookie:
        name = input("Enter the cookie name: ")
        if not name.strip():
            raise ValueError("Name cannot be empty.")

        while True:
            try:
                qty = int(input("Enter the quantity of cookies: "))
                if qty <= 0:
                    print("Quantity must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter an integer.")

        while True:
            try:
                price = float(input("Enter the price per dozen: "))
                if price <= 0:
                    print("Price must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")

        return Cookie(name, qty, price)

    def user_prompt_icecream(self) -> IceCream:
        name = input("Enter the icecream flavor: ")
        if not name.strip():
            raise ValueError("Name cannot be empty.")

        while True:
            try:
                scoops = int(input("Enter the number of scoops: "))
                if scoops <= 0:
                    print("Scoops must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter an integer.")

        while True:
            try:
                price = float(input("Enter the price per scoop: "))
                if price <= 0:
                    print("Price must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")

        return IceCream(name, scoops, price)

    def user_prompt_sundae(self) -> Sundae:
        name = input("Enter the icecream flavor: ")
        if not name.strip():
            raise ValueError("Name cannot be empty.")

        while True:
            try:
                scoops = int(input("Enter number of scoops: "))
                if scoops <= 0:
                    print("Scoops must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter an integer.")

        while True:
            try:
                price = float(input("Enter price per scoop: "))
                if price <= 0:
                    print("Price must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")

        topping = input("Enter the topping name: ")
        if not topping.strip():
            raise ValueError("Topping name cannot be empty.")

        while True:
            try:
                t_price = float(input("Enter the price of the topping: "))
                if t_price <= 0:
                    print("Topping price must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")

        return Sundae(name, scoops, price, topping, t_price)


def main() -> None:
    shop = DessertShop()
    order = Order()

    done = False
    prompt = (
        "\n1: Candy"
        "\n2: Cookie"
        "\n3: Ice Cream"
        "\n4: Sundae"
        "\n\nWhat would you like to add to the order? (1-4, Enter for done): "
    )

    while not done:
        choice = input(prompt)
        match choice.strip():
            case "":
                done = True
            case "1":
                item = shop.user_prompt_candy()
                order.add(item)
                print(f"{item.name} has been added to your order.")
            case "2":
                item = shop.user_prompt_cookie()
                order.add(item)
                print(f"{item.name} has been added to your order.")
            case "3":
                item = shop.user_prompt_icecream()
                order.add(item)
                print(f"{item.name} has been added to your order.")
            case "4":
                item = shop.user_prompt_sundae()
                order.add(item)
                print(f"{item.name} has been added to your order.")
            case _:
                print("Invalid response: Please enter a choice from the menu (1-4) or Enter")

    print()
    print(tabulate(order.to_list(), headers=["Name", "Cost", "Tax"], tablefmt="fsql"))


if __name__ == "__main__":
    main()
