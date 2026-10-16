"""Check tracked project files for the repository's visual style rules."""

from __future__ import annotations

import colorsys
import re
import subprocess
import sys
from pathlib import Path


EMOJI_RANGES = (
    (0x00A9, 0x00A9),
    (0x00AE, 0x00AE),
    (0x203C, 0x203C),
    (0x2049, 0x2049),
    (0x2122, 0x2122),
    (0x2139, 0x2139),
    (0x2194, 0x21FF),
    (0x1F000, 0x1FAFF),
    (0x1FC00, 0x1FFFD),
    (0x2600, 0x27BF),
    (0x2300, 0x23FF),
    (0x24C2, 0x24C2),
    (0x25AA, 0x25FE),
    (0x2934, 0x2935),
    (0x2B05, 0x2B55),
    (0x3030, 0x3030),
    (0x303D, 0x303D),
    (0x3297, 0x3299),
    (0xFE0F, 0xFE0F),
    (0x1F1E6, 0x1F1FF),
    (0x1F3FB, 0x1F3FF),
)
HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
RADIUS = re.compile(r"border-radius\s*:\s*([^;{}]+)", re.IGNORECASE)
PIXELS = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*px\b", re.IGNORECASE)
HTML_CALL = re.compile(r"st\.html\s*\(", re.IGNORECASE)


def tracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], check=True, capture_output=True
    )
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]


def is_data_file(path: Path) -> bool:
    parts = path.parts
    if len(parts) >= 3 and parts[:2] == ("data", "eval") and path.suffix.lower() == ".csv":
        return True
    return any(part.lower() in {"raw", "raw_data", "dataset"} for part in parts)


def is_emoji(character: str) -> bool:
    value = ord(character)
    return any(start <= value <= end for start, end in EMOJI_RANGES)


def is_purple(hex_color: str) -> bool:
    digits = hex_color[1:]
    if len(digits) in (3, 4):
        red, green, blue = (int(char * 2, 16) for char in digits[:3])
    else:
        red, green, blue = (
            int(digits[index:index + 2], 16) for index in (0, 2, 4)
        )
    hue, saturation, _ = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    degrees = hue * 360
    return 240 <= degrees <= 300 and saturation > 0.3


def visual_lines(path: Path, lines: list[str]) -> set[int]:
    suffix = path.suffix.lower()
    if suffix in {".css", ".scss", ".html", ".htm"}:
        return set(range(1, len(lines) + 1))
    if suffix != ".py":
        return set()

    enabled = False
    relevant: set[int] = set()
    for line_number, line in enumerate(lines, 1):
        if HTML_CALL.search(line):
            enabled = True
        if enabled:
            relevant.add(line_number)
            if ")" in line and ('"""' in line or "'''" in line):
                enabled = False
    return relevant


def inspect(path: Path) -> list[tuple[int, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    lines = content.splitlines()
    visual = visual_lines(path, lines)
    findings: list[tuple[int, str]] = []
    for number, line in enumerate(lines, 1):
        if "\u2014" in line:
            findings.append((number, "em dash"))
        if "\u2013" in line:
            findings.append((number, "en dash"))
        if any(is_emoji(character) for character in line):
            findings.append((number, "emoji"))

        if number not in visual:
            continue
        if re.search(r"gradient", line, re.IGNORECASE):
            findings.append((number, "gradient"))
        for radius in RADIUS.finditer(line):
            if any(float(value) > 6 for value in PIXELS.findall(radius.group(1))):
                findings.append((number, "border-radius above 6px"))
        for color in HEX_COLOR.findall(line):
            if is_purple(color):
                findings.append((number, f"purple hex color {color}"))
    return findings


def main() -> int:
    failures: list[tuple[str, int, str]] = []
    for path in tracked_paths():
        if is_data_file(path):
            continue
        failures.extend((path.as_posix(), line, rule) for line, rule in inspect(path))

    for filename, line, rule in failures:
        print(f"{filename}:{line}: {rule}")
    if failures:
        print(f"style check failed: {len(failures)} issue(s)")
        return 1
    print("style check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
