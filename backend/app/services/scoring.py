def calculate_score(time_limit_seconds: int, elapsed_seconds: float) -> int:
    """Points for a correct answer, proportionally reduced by how long the player took.

    Max 100 (answered instantly), 0 if answered at or after the time limit.
    Wrong answers must never call this function — always return 0 directly.
    """
    if elapsed_seconds >= time_limit_seconds:
        return 0
    return max(0, round(100 * (time_limit_seconds - elapsed_seconds) / time_limit_seconds))
