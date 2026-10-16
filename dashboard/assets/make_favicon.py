"""Generate the dashboard favicon with only the Python standard library."""

import struct
import zlib
from pathlib import Path


SIZE = 64
BACKGROUND = (245, 246, 248, 255)
ACCENT = (23, 107, 103, 255)
WHITE = (255, 255, 255, 255)


def pixel(x: int, y: int) -> tuple[int, int, int, int]:
    # A simple shield with a centered check, drawn with integer geometry.
    inside = 10 <= x <= 53 and 7 <= y <= 47 and y >= 7 + abs(x - 31) // 2
    if inside:
        color = ACCENT
        check = (22 <= x <= 29 and 28 <= y <= 35 and abs((x - 25) - (y - 30)) <= 2)
        check = check or (28 <= x <= 43 and 19 <= y <= 34 and abs((x - 34) + (y - 27)) <= 2)
        return WHITE if check else color
    return BACKGROUND


def chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def main() -> None:
    scanlines = b"".join(b"\x00" + bytes(channel for x in range(SIZE) for channel in pixel(x, y)) for y in range(SIZE))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(scanlines, 9))
    png += chunk(b"IEND", b"")
    target = Path(__file__).with_name("favicon.png")
    target.write_bytes(png)


if __name__ == "__main__":
    main()
