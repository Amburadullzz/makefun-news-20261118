#!/usr/bin/env python3
"""Write the entry image to /output/entry.png.

The image is drawn ahead of time by render.py and committed as entry.png, so the
graded program is a deterministic copy: two runs of it write the same bytes, and
it needs no network, no fonts and no Pillow at grade time.

The copy is checked against the caps the bounty sets (a whole PNG of at most
1 MiB and at most 1024 by 1024 pixels) so a broken commit fails loudly here
instead of at the gate.
"""

import os
import shutil
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
MAX_BYTES = 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def image_size(path: str) -> tuple[int, int]:
    """Read width and height from a PNG's IHDR chunk."""
    with open(path, "rb") as handle:
        head = handle.read(24)
    if not head.startswith(PNG_SIGNATURE) or head[12:16] != b"IHDR":
        raise SystemExit(f"entry.png is not a PNG: {path}")
    return struct.unpack(">II", head[16:24])


def main() -> None:
    size = os.path.getsize(SOURCE)
    if size > MAX_BYTES:
        raise SystemExit(f"entry.png is {size} bytes, over the 1 MiB cap")
    width, height = image_size(SOURCE)
    if width > 1024 or height > 1024:
        raise SystemExit(f"entry.png is {width}x{height}, over 1024x1024")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    shutil.copyfile(SOURCE, os.path.join(OUTPUT_DIR, "entry.png"))


if __name__ == "__main__":
    main()
