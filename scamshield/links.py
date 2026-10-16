from typing import Set
from scamshield.schemas import Extracted, CheckResult


def check(ext: Extracted, use_reputation: bool, blocklist: Set[str]) -> CheckResult:
    # name="links"
    raise NotImplementedError
