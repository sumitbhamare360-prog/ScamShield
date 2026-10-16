from typing import List, Dict, Set, Any


def init_db(path: str) -> None:
    raise NotImplementedError


def save_scan(masked_text: str, channel: str, verdict: Dict[str, Any]) -> int:
    raise NotImplementedError


def list_scans(limit: int = 50) -> List[Dict[str, Any]]:
    raise NotImplementedError


def delete_scan(scan_id: int) -> None:
    raise NotImplementedError


def clear_history() -> None:
    raise NotImplementedError


def save_feedback(scan_id: int, label: str) -> None:
    raise NotImplementedError


def add_blocklist(kind: str, value: str) -> None:
    raise NotImplementedError


def get_blocklist() -> Set[str]:
    raise NotImplementedError
