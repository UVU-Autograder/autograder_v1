from dessert import Order, Candy, Cookie, IceCream, Sundae
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
                scoops = int(input("Enter the scoop count: "))
                if scoops <= 0:
                    print("Scoop count must be greater than 0.")
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
                scoops = int(input("Enter the scoop count: "))
                if scoops <= 0:
                    print("Scoop count must be greater than 0.")
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
        topping_name = input("Enter the topping name: ")
        if not topping_name.strip():
            raise ValueError("Topping name cannot be empty.")
        while True:
            try:
                topping_price = float(input("Enter the topping price: "))
                if topping_price <= 0:
                    print("Topping price must be greater than 0.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number value.")
        return Sundae(name, scoops, price, topping_name, topping_price)


def main() -> None:
    shop = DessertShop()
    order = Order()

    while True:
        print("\n1: Candy\n2: Cookie\n3: Ice Cream\n4: Sundae\n5: Done")
        choice = input("What would you like to add to your order? (1-5): ")
        match choice.strip():
            case "1":
                order.add(shop.user_prompt_candy())
            case "2":
                order.add(shop.user_prompt_cookie())
            case "3":
                order.add(shop.user_prompt_icecream())
            case "4":
                order.add(shop.user_prompt_sundae())
            case "5":
                break
            case _:
                print("Invalid choice. Please enter a number 1-5.")

    while True:
        pay_choice = input("Enter payment method (CASH, CARD, PHONE): ").strip().upper()
        try:
            order.set_pay_type(pay_choice)  # type: ignore
            break
        except ValueError:
            print("Invalid payment method. Please enter CASH, CARD, or PHONE.")

    headers = ["Name", "Packaging", "Cost", "Tax"]
    print("\n" + tabulate(order.to_list(), headers=headers, tablefmt="fsql"))
    print(f"Total items in order: {len(order)}")
    print(f"Order Subtotal: ${order.order_cost():.2f}")
    print(f"Order Tax: ${order.order_tax():.2f}")
    print(f"Order Total: ${order.total_cost():.2f}")
    print(f"Paid with: {order.get_pay_type()}")


if __name__ == "__main__":
    main()
