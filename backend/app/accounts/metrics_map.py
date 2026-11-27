"""The one number worth trending for each task in this service."""
from typing import Callable, Dict, Optional, Tuple


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _left_probability(result: dict) -> Optional[float]:
    p = _number(result.get("p_left"))
    return None if p is None else round(p * 100, 1)


METRICS: Dict[str, Tuple[str, str, Callable[[dict], Optional[float]]]] = {
    "dominance": ("Left-dominance probability", "%", _left_probability),
}
