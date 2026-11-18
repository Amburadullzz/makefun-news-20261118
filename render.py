#!/usr/bin/env python3
"""Draw the one-image summary of 18 November 2026 world news.

Everything is drawn at 3x and downsampled, so edges and type stay clean at the
1024x1024 size the bounty allows.  Pure Pillow, no network, no randomness.

Layout rules kept by construction:
  * every string is shrunk until it fits its box, and every block is shrunk until
    it fits its line budget, so nothing is ever truncated;
  * each block records its bounding box in AUDIT, and audit_layout() fails loudly
    if two blocks overlap or a block leaves its card.
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 3                     # supersample factor
W = H = 1024 * S          # working canvas
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")

INK = (10, 14, 26)
CARD = (22, 30, 48)
CARD_2 = (28, 38, 60)
PAPER = (245, 242, 233)
MUTED = (150, 160, 182)
AMBER = (240, 178, 62)
RED = (214, 66, 58)
TEAL = (54, 190, 168)
BLUE = (70, 120, 210)
STEEL = (120, 134, 160)

AUDIT: list[tuple[str, tuple[float, float, float, float]]] = []


def px(v: float) -> int:
    return int(round(v * S))


def font(path: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, px(size))


def text_w(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont) -> float:
    box = d.textbbox((0, 0), text, font=f)
    return (box[2] - box[0]) / S


def line_h(size: float, factor: float = 1.14) -> float:
    return size * factor


def fit(d: ImageDraw.ImageDraw, text: str, path: str, size: float, max_w: float,
        min_size: float = 8) -> ImageFont.FreeTypeFont:
    """Largest font at or below `size` whose rendering of `text` fits max_w."""
    s = size
    while s > min_size:
        f = font(path, s)
        if text_w(d, text, f) <= max_w:
            return f
        s -= 1
    return font(path, min_size)


def wrap(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont,
         max_w: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(d, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(d: ImageDraw.ImageDraw, text: str, path: str, size: float,
              max_w: float, max_lines: int, min_size: float = 8):
    """Font + wrapped lines such that the text fits max_w and max_lines."""
    s = size
    while s > min_size:
        f = font(path, s)
        lines = wrap(d, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        s -= 1
    f = font(path, min_size)
    return f, wrap(d, text, f, max_w)[:max_lines]


def tracked(d: ImageDraw.ImageDraw, xy, text: str, f: ImageFont.FreeTypeFont,
            fill, track: float = 2.0) -> float:
    x, y = xy
    for ch in text:
        d.text((px(x), px(y)), ch, font=f, fill=fill)
        x += text_w(d, ch, f) + track
    return x


def card(d: ImageDraw.ImageDraw, x, y, w, h, fill=CARD, radius=14):
    d.rounded_rectangle([px(x), px(y), px(x + w), px(y + h)], radius=px(radius), fill=fill)


def vgrad(img: Image.Image, box, top, bottom):
    x0, y0, x1, y1 = [px(v) for v in box]
    grad = Image.new("RGB", (1, max(1, y1 - y0)))
    gd = ImageDraw.Draw(grad)
    for i in range(y1 - y0):
        t = i / max(1, y1 - y0 - 1)
        gd.point((0, i), fill=tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)))
    img.paste(grad.resize((max(1, x1 - x0), max(1, y1 - y0))), (x0, y0))


def note(name: str, x, y, w, h) -> None:
    AUDIT.append((name, (x, y, x + w, y + h)))


# ---------------------------------------------------------------- illustrations
def flag_us(d, x, y, w, h):
    stripes = 7
    for i in range(stripes):
        d.rectangle([px(x), px(y + i * h / stripes), px(x + w), px(y + (i + 1) * h / stripes)],
                    fill=RED if i % 2 == 0 else PAPER)
    d.rectangle([px(x), px(y), px(x + w * 0.42), px(y + h * 4 / stripes)], fill=BLUE)
    for r in range(3):
        for c in range(4):
            cx = x + w * 0.42 * (c + 0.7) / 4.4
            cy = y + h * 4 / stripes * (r + 0.7) / 3.4
            d.ellipse([px(cx - 1.6), px(cy - 1.6), px(cx + 1.6), px(cy + 1.6)], fill=PAPER)


def flag_cn(d, x, y, w, h):
    d.rectangle([px(x), px(y), px(x + w), px(y + h)], fill=(198, 40, 40))
    d.ellipse([px(x + w * 0.14), px(y + h * 0.22), px(x + w * 0.34), px(y + h * 0.62)], fill=AMBER)
    for fx, fy in ((0.44, 0.14), (0.52, 0.28), (0.52, 0.46), (0.44, 0.58)):
        cx, cy = x + w * fx, y + h * fy
        d.ellipse([px(cx - 2.6), px(cy - 2.6), px(cx + 2.6), px(cy + 2.6)], fill=AMBER)


def flag_ru(d, x, y, w, h):
    d.rectangle([px(x), px(y), px(x + w), px(y + h / 3)], fill=PAPER)
    d.rectangle([px(x), px(y + h / 3), px(x + w), px(y + 2 * h / 3)], fill=(42, 82, 160))
    d.rectangle([px(x), px(y + 2 * h / 3), px(x + w), px(y + h)], fill=RED)


def icon_hormuz(d, x, y, s):
    d.rectangle([px(x), px(y), px(x + s), px(y + s)], fill=(16, 34, 56))
    d.polygon([(px(x), px(y)), (px(x + s * 0.46), px(y)), (px(x + s * 0.30), px(y + s * 0.46)),
               (px(x + s * 0.44), px(y + s * 0.74)), (px(x), px(y + s * 0.86))], fill=(66, 58, 40))
    d.polygon([(px(x + s), px(y + s * 0.30)), (px(x + s * 0.66), px(y + s * 0.44)),
               (px(x + s * 0.74), px(y + s * 0.66)), (px(x + s), px(y + s * 0.74))], fill=(66, 58, 40))
    tx, ty = x + s * 0.50, y + s * 0.60
    d.polygon([(px(tx), px(ty)), (px(tx + s * 0.30), px(ty)), (px(tx + s * 0.25), px(ty + s * 0.09)),
               (px(tx + s * 0.05), px(ty + s * 0.09))], fill=(206, 212, 224))
    d.rectangle([px(tx + s * 0.21), px(ty - s * 0.07), px(tx + s * 0.26), px(ty)], fill=(206, 212, 224))
    d.arc([px(x + s * 0.02), px(y - s * 0.30), px(x + s * 0.80), px(y + s * 0.60)],
          start=300, end=350, fill=RED, width=px(2.4))
    d.arc([px(x + s * 0.10), px(y - s * 0.16), px(x + s * 0.92), px(y + s * 0.74)],
          start=305, end=352, fill=AMBER, width=px(2.0))


def icon_bridge(d, x, y, s):
    d.rectangle([px(x), px(y), px(x + s), px(y + s)], fill=(18, 30, 48))
    d.rectangle([px(x), px(y + s * 0.66), px(x + s), px(y + s)], fill=(24, 52, 78))
    for i in range(3):
        yy = y + s * (0.74 + i * 0.08)
        d.line([px(x), px(yy), px(x + s), px(yy)], fill=(40, 74, 104), width=px(1.2))
    d.rectangle([px(x), px(y + s * 0.34), px(x + s * 0.40), px(y + s * 0.44)], fill=STEEL)
    d.rectangle([px(x + s * 0.62), px(y + s * 0.34), px(x + s), px(y + s * 0.44)], fill=STEEL)
    d.rectangle([px(x + s * 0.40), px(y + s * 0.50), px(x + s * 0.52), px(y + s * 0.56)], fill=(60, 74, 96))
    for fx in (0.16, 0.32, 0.70, 0.86):
        d.rectangle([px(x + s * fx), px(y + s * 0.44), px(x + s * (fx + 0.04)), px(y + s * 0.68)],
                    fill=(88, 100, 124))
    for fx in (0.10, 0.26, 0.76, 0.92):
        d.line([px(x + s * fx), px(y + s * 0.34), px(x + s * (fx + 0.02)), px(y + s * 0.12)],
               fill=(150, 160, 182), width=px(1.2))


def icon_measles(d, x, y, s):
    d.rectangle([px(x), px(y), px(x + s), px(y + s)], fill=(40, 20, 26))
    cx, cy, r = x + s * 0.32, y + s * 0.44, s * 0.19
    d.ellipse([px(cx - r), px(cy - r), px(cx + r), px(cy + r)], fill=RED)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        d.ellipse([px(cx + math.cos(rad) * r * 1.20 - s * 0.035),
                   px(cy + math.sin(rad) * r * 1.20 - s * 0.035),
                   px(cx + math.cos(rad) * r * 1.20 + s * 0.035),
                   px(cy + math.sin(rad) * r * 1.20 + s * 0.035)], fill=RED)
    d.ellipse([px(cx - r * 0.34), px(cy - r * 0.34), px(cx + r * 0.34), px(cy + r * 0.34)], fill=(90, 24, 28))
    for i, hh in enumerate((0.16, 0.28, 0.42, 0.60)):
        bx = x + s * (0.62 + i * 0.09)
        d.rectangle([px(bx), px(y + s * (0.82 - hh)), px(bx + s * 0.055), px(y + s * 0.82)],
                    fill=(226, 120, 108))


def icon_mongolia(d, x, y, s):
    d.rectangle([px(x), px(y), px(x + s), px(y + s)], fill=(18, 30, 44))
    fx, fy, fw, fh = x + s * 0.08, y + s * 0.12, s * 0.84, s * 0.38
    d.rectangle([px(fx), px(fy), px(fx + fw / 3), px(fy + fh)], fill=RED)
    d.rectangle([px(fx + fw / 3), px(fy), px(fx + 2 * fw / 3), px(fy + fh)], fill=(44, 92, 168))
    d.rectangle([px(fx + 2 * fw / 3), px(fy), px(fx + fw), px(fy + fh)], fill=RED)
    d.ellipse([px(fx + fw / 6 - s * 0.05), px(fy + fh * 0.26), px(fx + fw / 6 + s * 0.05),
               px(fy + fh * 0.64)], fill=AMBER)
    gx, gy = x + s * 0.50, y + s * 0.88
    d.polygon([(px(gx - s * 0.20), px(gy)), (px(gx + s * 0.20), px(gy)),
               (px(gx + s * 0.16), px(gy - s * 0.20)), (px(gx), px(gy - s * 0.34)),
               (px(gx - s * 0.16), px(gy - s * 0.20))], fill=(206, 212, 224))
    d.rectangle([px(gx - s * 0.05), px(gy - s * 0.10), px(gx + s * 0.05), px(gy)], fill=(120, 40, 40))


# ---------------------------------------------------------------- composition
def build() -> Image.Image:
    img = Image.new("RGB", (W, H), INK)
    vgrad(img, (0, 0, 1024, 1024), (14, 20, 36), (7, 10, 20))
    d = ImageDraw.Draw(img)

    # ---- masthead -----------------------------------------------------------
    tracked(d, (64, 44), "THE WORLD IN ONE DAY", font(SANS_B, 15), AMBER, track=4.2)
    d.text((px(62), px(64)), "18 NOVEMBER 2026", font=font(SERIF_B, 60), fill=PAPER)
    note("date", 62, 64, 640, 74)
    tracked(d, (66, 144), "WEDNESDAY \u00b7 SEVEN STORIES \u00b7 FOUR CONTINENTS",
            font(SANS, 17), MUTED, track=1.6)
    d.rectangle([px(64), px(178), px(960), px(181)], fill=(60, 70, 94))
    d.rectangle([px(64), px(185), px(960), px(186)], fill=(60, 70, 94))

    # ---- lead story: Trump to China, first trilateral with Xi and Putin ------
    card(d, 64, 202, 896, 296, CARD)
    ax, ay, aw, ah = 84, 222, 350, 256
    d.rounded_rectangle([px(ax), px(ay), px(ax + aw), px(ay + ah)], radius=px(10), fill=(15, 22, 40))
    d.ellipse([px(ax + 55), px(ay + 166), px(ax + 295), px(ay + 238)], fill=(38, 48, 72))
    d.ellipse([px(ax + 68), px(ay + 174), px(ax + 282), px(ay + 228)], fill=(26, 34, 54))
    for fx, painter in ((0.20, flag_us), (0.50, flag_cn), (0.80, flag_ru)):
        cx = ax + aw * fx
        d.rectangle([px(cx - 1.2), px(ay + 58), px(cx + 1.2), px(ay + 174)], fill=(120, 130, 150))
        painter(d, cx - 30, ay + 32, 60, 40)
    for fx, label in ((0.20, "US"), (0.50, "CN"), (0.80, "RU")):
        cx = ax + aw * fx
        f = font(SANS_B, 12)
        w = text_w(d, label, f)
        d.text((px(cx - w / 2), px(ay + 190)), label, font=f, fill=(196, 204, 220))
    d.ellipse([px(ax + 120), px(ay + 148), px(ax + 230), px(ay + 188)], fill=(44, 56, 84))

    tx, tw = 470, 462
    tracked(d, (tx, 226), "GEOPOLITICS", font(SANS_B, 13), AMBER, track=3.0)
    head = "TRUMP FLIES TO CHINA FOR FIRST THREE-WAY TALKS"
    f_head, head_lines = fit_block(d, head, SANS_B, 34, tw, 3)
    y = 250
    for ln in head_lines:
        d.text((px(tx), px(y)), ln, font=f_head, fill=PAPER)
        y += line_h(f_head.size / S)
    note("lead-head", tx, 250, tw, y - 250)
    sub = ("Xi Jinping and Vladimir Putin join him at Shenzhen on Thursday, with arms "
           "control, Ukraine and Iran on the table.")
    f_sub, sub_lines = fit_block(d, sub, SANS, 17, tw - 4, 3)
    yy = y + 10
    for ln in sub_lines:
        d.text((px(tx), px(yy)), ln, font=f_sub, fill=(196, 204, 220))
        yy += line_h(f_sub.size / S, 1.30)
    note("lead-sub", tx, y + 10, tw, yy - y - 10)
    if yy + 22 < 490:
        tracked(d, (tx, yy + 6), "FIRST TRILATERAL OF ITS KIND", font(SANS_B, 13), TEAL, track=1.4)

    # ---- four story cards ---------------------------------------------------
    stories = [
        ("MIDDLE EAST", "US STRIKES IRAN'S QESHM ISLAND",
         "Reply to a third drone attack on Bahrain in five days; tankers burn in Hormuz.",
         icon_hormuz),
        ("EUROPE", "CRIMEAN BRIDGE ARCH DESTROYED",
         "Ukrainian drones and missiles cut Russia's road link to the peninsula.",
         icon_bridge),
        ("AMERICAS", "US LOSES MEASLES-FREE STATUS",
         "First time in 26 years, with more than 5,400 cases and ten deaths.",
         icon_measles),
        ("ASIA", "MONGOLIA'S PRESIDENT RESIGNS",
         "Ukhnaa Khurelsukh quits over abuse-of-power and bribery claims.",
         icon_mongolia),
    ]
    cw, ch = 436, 172
    positions = [(64, 516), (524, 516), (64, 706), (524, 706)]
    for (kick, head, body, icon), (cx, cy) in zip(stories, positions):
        card(d, cx, cy, cw, ch, CARD_2, radius=12)
        icon(d, cx + 16, cy + 16, 92)
        d.rounded_rectangle([px(cx + 16), px(cy + 16), px(cx + 108), px(cy + 108)],
                            radius=px(8), outline=(48, 60, 86), width=px(1.2))
        txx = cx + 124
        maxw = cw - 124 - 16
        tracked(d, (txx, cy + 16), kick, font(SANS_B, 11), AMBER, track=2.0)
        fh, hl = fit_block(d, head, SANS_B, 24, maxw, 2, min_size=15)
        yy = cy + 34
        for ln in hl:
            d.text((px(txx), px(yy)), ln, font=fh, fill=PAPER)
            yy += line_h(fh.size / S)
        note("card-head:" + kick, txx, cy + 34, maxw, yy - cy - 34)
        body_y0 = yy
        fb, bl = fit_block(d, body, SANS, 13.5, maxw, 3, min_size=10)
        for ln in bl:
            d.text((px(txx), px(yy + 3)), ln, font=fb, fill=(178, 188, 208))
            yy += line_h(fb.size / S, 1.30)
        note("card-body:" + kick, txx, body_y0, maxw, yy - body_y0)

    # ---- briefs strip -------------------------------------------------------
    d.rectangle([px(64), px(892), px(960), px(895)], fill=(60, 70, 94))
    briefs = [
        ("ISRAEL", "Parliament elects Matan Kahana, a Netanyahu opponent, as speaker, 66 to 52."),
        ("BUSINESS", "Nvidia beats forecasts and keeps Jensen Huang out after his abrupt exit."),
        ("RUSSIA", "An An-12 military transport crashes in Siberia, killing all 19 aboard."),
    ]
    by = 906
    for kick, text in briefs:
        tracked(d, (64, by), kick, font(SANS_B, 10), TEAL, track=1.6)
        fb = font(SANS, 12.5)
        d.text((px(146), px(by - 1)), text, font=fb, fill=(186, 196, 214))
        note("brief:" + kick, 64, by, 146 + text_w(d, text, fb) - 64, 14)
        by += 27

    tracked(d, (64, 994), "MAKEFUN DAILY \u00b7 18 NOVEMBER 2026", font(SANS_B, 11),
            (110, 120, 142), track=2.2)
    return img


def audit_layout() -> list[str]:
    problems = []
    for i in range(len(AUDIT)):
        n1, a = AUDIT[i]
        if a[2] > 962 or a[3] > 1010:
            problems.append(f"{n1} leaves the page: {a}")
        for j in range(i + 1, len(AUDIT)):
            n2, b = AUDIT[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                problems.append(f"{n1} overlaps {n2}")
    return problems


def main() -> int:
    img = build()
    problems = audit_layout()
    for p in problems:
        print("LAYOUT:", p)
    img = img.resize((1024, 1024), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))
    img.save(OUT, format="PNG", optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes", "problems", len(problems))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
