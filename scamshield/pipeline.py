from typing import Set
from scamshield.schemas import Message, Verdict


def analyze(msg: Message, use_reputation: bool, blocklist: Set[str]) -> Verdict:
    raise NotImplementedError
