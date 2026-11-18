#!/usr/bin/env python3
"""Print a coarse ASCII luminance map of entry.png so the layout can be checked."""
import sys
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 96
img = Image.open(path).convert("L")
w, h = img.size
rows = max(1, int(cols * h / w / 2.1))
small = img.resize((cols, rows), Image.LANCZOS)
ramp = " .:-=+*#%@"
for y in range(rows):
    line = "".join(ramp[min(len(ramp) - 1, small.getpixel((x, y)) * len(ramp) // 256)]
                   for x in range(cols))
    print(f"{line}")
