from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def apply_discount(total, threshold=Decimal("100.00"), rate=Decimal("0.10")):
    total = Decimal(str(total))
    if total < 0:
        raise ValueError("Сумма заказа не может быть отрицательной")
    discount = (total * rate).quantize(CENT, ROUND_HALF_UP) if total >= threshold else Decimal("0.00")
    return discount, total - discount
