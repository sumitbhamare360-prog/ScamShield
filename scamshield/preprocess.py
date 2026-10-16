from scamshield.schemas import Message, Extracted


def mask(text: str) -> str:
    raise NotImplementedError


def extract(msg: Message) -> Extracted:
    raise NotImplementedError
