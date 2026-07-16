from dessert import Order, Candy, Cookie, IceCream, Sundae
from tabulate import tabulate

def main() -> None:
    order = Order()
    order.add(Candy("Candy Corn", 1.5, 0.25))
    order.add(Candy("Gummy Bears", 0.25, 0.35))
    order.add(Cookie("Chocolate Chip", 6, 3.99))
    order.add(IceCream("Pistachio", 2, 0.79))
    order.add(Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29))
    order.add(Cookie("Oatmeal Raisin", 2, 3.45))

    data = []
    for item in order:
        data.append([
            item.name,
            f"${item.calculate_cost():.2f}",
            f"${item.calculate_tax():.2f}"
        ])

    subtotal = order.order_cost()
    total_tax = order.order_tax()
    total = round(subtotal + total_tax, 2)

    data.append([
        "Order Subtotals",
        f"${subtotal:.2f}",
        f"${total_tax:.2f}"
    ])
    data.append([
        "Order Total",
        "",
        f"${total:.2f}"
    ])
    data.append([
        "Total Items in the order:",
        "",
        len(order)
    ])

    print(tabulate(data, headers=["Desserts", "Cost", "Tax"], tablefmt="fsql"))


if __name__ == "__main__":
    main()
