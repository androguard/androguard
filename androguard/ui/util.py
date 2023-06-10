def clamp(range_min: int, range_max: int, value: int) -> int:
    """Return value if its is within range_min and range_max else return the nearest bound"""
    return max(min(range_max, value), range_min)