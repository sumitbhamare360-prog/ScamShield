from typing import Callable, List, Dict, Any


def highlights(score_fn: Callable[[str], float], text: str) -> List[Dict[str, Any]]:
    # dict keys: text, start, end, weight
    raise NotImplementedError
