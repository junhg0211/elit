def linear(value, x0, y0, x1, y1) -> float:
    return (value - x0) / (y0 - x0) * (y1 - x1) + x1


def cubic(value, x0, y0, x1, y1) -> float:
    x = (value - x0) / (y0 - x0)
    return (3 - 2*x) * x**2 * (y1 - x1) + x1
