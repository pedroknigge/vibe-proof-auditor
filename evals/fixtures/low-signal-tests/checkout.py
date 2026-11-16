"""A checkout boundary with a deliberately omitted shipping charge."""


def item_subtotal(prices):
    return sum(prices)


def pay(prices, shipping_charge):
    """Charge the item subtotal plus the quoted shipping charge."""
    return item_subtotal(prices)  # planted defect: shipping_charge is ignored

