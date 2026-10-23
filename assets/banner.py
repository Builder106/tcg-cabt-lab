"""Write the README banners, assets/banner-light.svg and assets/banner-dark.svg.

The banners reuse the showcase's Glaxnimate art (mark, card back, card faces, hex tile) and
set every line of type as outlines from the site's own fonts, so GitHub draws Exo 2 and
Archivo without loading a font. Run from the repository root:

    uv run --no-project --with fonttools --with brotli --with uharfbuzz python assets/banner.py
    rsvg-convert -w 1200 -h 420 assets/banner-light.svg -o assets/banner-light.png
    rsvg-convert -w 1200 -h 420 assets/banner-dark.svg -o assets/banner-dark.png
"""

import io
import re
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "web/public/fonts"
ART = ROOT / "web/design/glaxnimate"
W, H, BAR = 1200, 420, 64

THEMES = {
    "dark": {
        "ground": "#1B1E23",
        "hex": "#2C3039",
        "ink": "#F2F4F7",
        "muted": "#AEB5C2",
        "glow": 0.22,
        "shadow": 0.45,
    },
    "light": {
        "ground": "#ECEEF2",
        "hex": "#D9DDE4",
        "ink": "#15171C",
        "muted": "#565C67",
        "glow": 0.12,
        "shadow": 0.22,
    },
}
# Deeper than the site's side colours so 14 px white labels clear 4.5:1
BLUE, RED = "#1F68C9", "#C41F2A"


def load(name, variations):
    font = TTFont(FONTS / name)
    font.flavor = None
    raw = io.BytesIO()
    font.save(raw)
    hb_font = hb.Font(hb.Face(raw.getvalue()))
    hb_font.set_variations(variations)
    return hb_font


EXO = load("exo-2-600_900-italic.woff2", {"wght": 900})
EXO_BAR = load("exo-2-600_900-italic.woff2", {"wght": 850})
ARCHIVO = load("archivo-100_900-normal.woff2", {"wght": 400})
ARCHIVO_BOLD = load("archivo-100_900-normal.woff2", {"wght": 600})


def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def shape(font, s):
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    return buf.glyph_infos, buf.glyph_positions


def width(font, s, size):
    _, pos = shape(font, s)
    return sum(p.x_advance for p in pos) * size / font.face.upem


def text(font, s, size, x, y, fill, anchor="start"):
    """One line of type as a single outlined path; y is the baseline."""
    infos, pos = shape(font, s)
    scale = size / font.face.upem
    if anchor == "end":
        x -= width(font, s, size)
    pen = SVGPathPen(None, ntos=num)
    cursor = 0
    for info, p in zip(infos, pos, strict=True):
        ox = x + (cursor + p.x_offset) * scale
        oy = y - p.y_offset * scale
        font.draw_glyph_with_pen(info.codepoint, TransformPen(pen, (scale, 0, 0, -scale, ox, oy)))
        cursor += p.x_advance
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


def inner(name, prefix):
    """The drawing inside a Glaxnimate SVG, minus its title, with ids made unique."""
    src = (ART / name).read_text()
    body = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", src.strip())
    body = re.sub(r"<title[^>]*>.*?</title>", "", body)
    return body.replace(' id="', f' id="{prefix}-')


def card(name, prefix, cx, cy, angle):
    w, h = 630 * 0.25, 880 * 0.25
    return (
        f'<g filter="url(#lift)" transform="translate({cx} {cy}) rotate({angle}) '
        f'translate({-w / 2} {-h / 2})"><svg width="{w}" height="{h}" viewBox="0 0 630 880">'
        f"{inner(name, prefix)}</svg></g>"
    )


def chip(x, y, fill, label, value):
    w = max(width(ARCHIVO_BOLD, label, 14), width(EXO, value, 30)) + 32
    return (
        f'<rect x="{x}" y="{y}" width="{num(w)}" height="62" rx="6" fill="{fill}"/>'
        + text(ARCHIVO_BOLD, label, 14, x + 16, y + 23, "#FFFFFF")
        + text(EXO, value, 30, x + 16, y + 52, "#FFFFFF")
    ), w


def banner(theme):
    t = THEMES[theme]
    muted = t["muted"]
    blue, blue_w = chip(56, 314, BLUE, "Fixed opponent pool", "58.3%")
    red, _ = chip(56 + blue_w + 12, 314, RED, "Diverse opponent pool", "57.8%")
    hex_path = re.search(r' d="([^"]+)"', (ART / "hex-dark.svg").read_text()).group(1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'role="img" aria-labelledby="banner-title">',
        '<title id="banner-title">TCG CABT Lab: compact agents for the Pokémon TCG. Fixed '
        "opponent pool 58.3%, diverse opponent pool 57.8% over 360 held-out games.</title>",
        "<defs>",
        f'<pattern id="hex" width="52" height="90" patternUnits="userSpaceOnUse" x="-6" y="{BAR}">'
        f'<path d="{hex_path}" fill="none" stroke="{t["hex"]}" stroke-width="2" '
        'stroke-linejoin="round"/></pattern>',
        '<radialGradient id="glow" cx="945" cy="250" r="330" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#2D7BE5" stop-opacity="{t["glow"]}"/>'
        '<stop offset="1" stop-color="#2D7BE5" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#DC2C33"/><stop offset="1" stop-color="#A8121A"/>'
        "</linearGradient>",
        '<filter id="lift" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#000" '
        f'flood-opacity="{t["shadow"]}"/></filter>',
        "</defs>",
        f'<rect width="{W}" height="{H}" fill="{t["ground"]}"/>',
        f'<rect y="{BAR}" width="{W}" height="{H - BAR}" fill="url(#hex)"/>',
        f'<rect y="{BAR}" width="{W}" height="{H - BAR}" fill="url(#glow)"/>',
        card("card-back.svg", "back", 830, 258, -15),
        card("face-psychic.svg", "psychic", 948, 234, -2),
        card("face-water.svg", "water", 1062, 262, 12),
        f'<rect width="{W}" height="{BAR}" fill="url(#bar)"/>',
        f'<rect y="{BAR}" width="{W}" height="3" fill="#7A0A10"/>',
        f'<g transform="translate(40 12) scale(0.625)">{inner("mark.svg", "mark")}</g>',
        text(EXO_BAR, "CABT LAB", 24, 92, 41, "#FFFFFF"),
        text(ARCHIVO_BOLD, "tcg-cabt-lab.vercel.app", 16, W - 40, 38, "#FFFFFF", "end"),
        text(EXO, "Compact agents for", 52, 56, 150, t["ink"]),
        text(EXO, "the Pokémon TCG", 52, 56, 208, t["ink"]),
        text(ARCHIVO, "Does training against varied opponents help on unseen", 20, 56, 254, muted),
        text(ARCHIVO, "decks? Over 360 held-out games, not measurably.", 20, 56, 282, muted),
        blue,
        red,
        "</svg>",
    ]
    (ROOT / f"assets/banner-{theme}.svg").write_text("".join(parts) + "\n")


for name in THEMES:
    banner(name)
