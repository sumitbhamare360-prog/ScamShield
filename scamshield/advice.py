from typing import Dict, List
from scamshield.schemas import Extracted, CheckResult, Verdict


def classify_scam_type(ext: Extracted, checks: Dict[str, CheckResult]) -> str:
    raise NotImplementedError


def actions(category: str, scam_type: str, ext: Extracted) -> List[str]:
    raise NotImplementedError


def report_text(verdict: Verdict) -> str:
    raise NotImplementedError
