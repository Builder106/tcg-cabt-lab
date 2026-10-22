"""Drawing script for the card faces.

Emits the element list passed to the Glaxnimate MCP tool glaxnimate_create_svg for each face,
and writes the SVG in the tool's serialization, so the faces can be rebuilt without retyping
path data. Usage: python3 faces.py elements <face>  |  python3 faces.py write
"""

import json
import math
import sys
from html import escape
from pathlib import Path

HERE = Path(__file__).parent

# name band, field tint, art ground, rules, foot band
TYPES = {
    "psychic": (
        "#6E44D6",
        "#EFE9FC",
        "#2A175E",
        "#C8B8F2",
        "#DCD0F6",
        "Psychic type: violet name band, art window of concentric rings",
    ),
    "water": (
        "#1F78D1",
        "#E6F1FC",
        "#0B3563",
        "#B5D5F5",
        "#CFE3F8",
        "Water: blue name band, art window of waves",
    ),
    "colorless": (
        "#6F7890",
        "#EEF0F4",
        "#3E4658",
        "#C9CED9",
        "#DDE1E8",
        "Colorless type: steel name band, art window of a hex lattice",
    ),
    "trainer": (
        "#2F3B55",
        "#ECEFF4",
        "#262E40",
        "#C4CAD6",
        "#D9DEE7",
        "Trainer: dark slate name band, art window of diagonal stripes",
    ),
    "trainer-plain": (
        "#2F3B55",
        "#ECEFF4",
        "#262E40",
        "#C4CAD6",
        "#D9DEE7",
        "Trainer in play: dark slate name band, art window of faint stripes, no printed rules",
    ),
}

FIELD = (
    "M35 0H595A35 35 0 0 1 630 35V845A35 35 0 0 1 595 880H35A35 35 0 0 1 0 845V35A35 35 0 0 1 35 0Z"
    "M56 148H574A12 12 0 0 1 586 160V468A12 12 0 0 1 574 480H56A12 12 0 0 1 44 468V160A12 12 0 0 1 56 148Z"
)


def num(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def el(kind, id_, children=None, text=None, **attrs):
    e = {
        "type": kind,
        "id": id_,
        "attributes": {k.replace("_", "-"): num(v) for k, v in attrs.items()},
    }
    if children is not None:
        e["children"] = children
    if text is not None:
        e["text"] = text
        del e["attributes"]
    return e


def art(face):
    if face == "psychic":
        shades = [
            "#8E5CF0",
            "#8253E6",
            "#7449D6",
            "#6640C4",
            "#5937B0",
            "#4C2F9C",
            "#41288A",
            "#372278",
        ]
        rings = [
            el(
                "circle",
                f"ring-{i + 1}",
                cx=315,
                cy=314,
                r=40 + 32 * i,
                fill="none",
                stroke=c,
                stroke_width=5,
            )
            for i, c in enumerate(shades)
        ]
        return [
            el("g", "art-rings", rings),
            el("path", "art-core", d="M315 290L339 314L315 338L291 314Z", fill="#C9B4FA"),
        ]
    if face == "water":
        d = ""
        for row in range(9):
            y = 170 + row * 38
            d += f"M46 {y}"
            x = 46
            while x < 584:
                d += f"Q{x + 17} {y - 12} {x + 34} {y}T{x + 68} {y}"
                x += 68
        return [
            el(
                "path",
                "art-waves",
                fill="none",
                stroke="#4FA3EE",
                stroke_width=5,
                stroke_linecap="round",
                d=d,
            )
        ]
    if face == "colorless":
        d, r = "", 34
        dx = r * math.sqrt(3)
        for row in range(8):
            for col in range(10):
                cx = 46 + col * dx + (dx / 2 if row % 2 else 0)
                cy = 148 + row * r * 1.5
                pts = [
                    (
                        cx + r * math.cos(math.radians(60 * i + 30)),
                        cy + r * math.sin(math.radians(60 * i + 30)),
                    )
                    for i in range(6)
                ]
                d += "M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in pts) + "Z"
        return [el("path", "art-hex", fill="none", stroke="#8C95A8", stroke_width=4, d=d)]
    d = "".join(f"M{46 + i * 28} 148L{46 + i * 28 + 330} 478" for i in range(-12, 20))
    faint = face == "trainer-plain"
    return [
        el(
            "path",
            "art-stripes",
            fill="none",
            stroke="#2D3649" if faint else "#3A4560",
            stroke_width=10,
            d=d,
        )
    ]


def elements(face):
    band, tint, ground, rule, foot, title = TYPES[face]
    return [
        el("title", "face-title", text=f"Card face, {title}"),
        el("rect", "art-ground", x=44, y=148, width=542, height=332, fill=ground),
        *art(face),
        el("path", "face-field", fill=tint, fill_rule="evenodd", d=FIELD),
        el(
            "rect",
            "face-border",
            x=9,
            y=9,
            width=612,
            height=862,
            rx=26,
            fill="none",
            stroke="#E8ECF2",
            stroke_width=18,
        ),
        el("rect", "name-band", x=18, y=18, width=594, height=112, rx=22, fill=band),
        el("rect", "name-band-base", x=18, y=92, width=594, height=38, fill=band),
        el(
            "rect",
            "art-border",
            x=44,
            y=148,
            width=542,
            height=332,
            rx=12,
            fill="none",
            stroke="#FFFFFF",
            stroke_width=6,
        ),
        *(
            []
            if face == "trainer-plain"
            else [
                el("rect", "rule-1", x=44, y=628, width=542, height=2, fill=rule),
                el("rect", "rule-2", x=44, y=744, width=542, height=2, fill=rule),
            ]
        ),
        el("rect", "foot-band", x=18, y=804, width=594, height=58, rx=22, fill=foot),
        el("circle", "set-mark", cx=574, cy=833, r=12, fill="none", stroke=band, stroke_width=3),
    ]


ENERGY = {
    "energy-psychic": ("#6E44D6", "#4E2DA8", "Psychic Energy: violet field with the Psychic glyph"),
    "energy-water": ("#1F78D1", "#145BA6", "Water Energy: blue field with the Water glyph"),
}


def energy_elements(face):
    field, band, title = ENERGY[face]
    if face == "energy-psychic":
        glyph = [
            el(
                "circle",
                "glyph-ring",
                cx=12,
                cy=12,
                r=6.2,
                fill="none",
                stroke="#FFFFFF",
                stroke_width=2,
            ),
            el("path", "glyph-core", d="M12 9.2L14.8 12L12 14.8L9.2 12Z", fill="#FFFFFF"),
        ]
    else:
        glyph = [
            el(
                "path",
                "glyph-waves",
                fill="none",
                stroke="#FFFFFF",
                stroke_width=1.8,
                stroke_linecap="round",
                d="M6 9.2C7.5 7.9 9 7.9 10.5 9.2S13.5 10.5 15 9.2 16.5 7.9 18 9.2M6 13C7.5 11.7 9 11.7 10.5 13S13.5 14.3 15 13 16.5 11.7 18 13M8 16.8C9.2 15.7 10.6 15.7 12 16.8S14.8 17.9 16 16.8",
            )
        ]
    return [
        el("title", "face-title", text=f"Card face, {title}"),
        el("rect", "face-ground", x=0, y=0, width=630, height=880, rx=35, fill="#E8ECF2"),
        el("rect", "face-field", x=18, y=18, width=594, height=844, rx=22, fill=field),
        el("rect", "name-band", x=18, y=18, width=594, height=112, rx=22, fill=band),
        el("rect", "name-band-base", x=18, y=92, width=594, height=38, fill=band),
        el("circle", "glyph-halo", cx=315, cy=470, r=230, fill="#FFFFFF", fill_opacity=0.1),
        el("circle", "glyph-disc", cx=315, cy=470, r=176, fill="#FFFFFF", fill_opacity=0.14),
        el("g", "glyph", glyph, transform="translate(315 470) scale(15) translate(-12 -12)"),
        el(
            "circle",
            "set-mark",
            cx=574,
            cy=833,
            r=12,
            fill="none",
            stroke="#FFFFFF",
            stroke_width=3,
        ),
    ]


# Sort art: the art window of each sort card, 542 x 332, drawn in the upper right so the card
# name can sit bottom left. Ids carry the sort key so all eight can share a page; the site
# animates them by id. Pool colours match the table's piles: fixed blue, diverse red.
ART_W, ART_H = 542, 332
BLUE, RED, GOLD, WHITE = "#2D7BE5", "#E0343F", "#F6C445", "#FFFFFF"
SHADE = {BLUE: "#1C5BB4", RED: "#A92330", GOLD: "#C98A12"}
LIGHT = {BLUE: "#6FA6F2", RED: "#F07A82", GOLD: "#FADB8A"}


def ground(k, inner, outer, cx=400, cy=80):
    return [
        el(
            "defs",
            f"{k}-defs",
            [
                el(
                    "radialGradient",
                    f"{k}-glow",
                    [
                        el("stop", f"{k}-glow-in", offset=0, stop_color=inner),
                        el("stop", f"{k}-glow-out", offset=1, stop_color=outer),
                    ],
                    cx=cx,
                    cy=cy,
                    r=420,
                    gradientUnits="userSpaceOnUse",
                )
            ],
        ),
        el("rect", f"{k}-ground", x=0, y=0, width=ART_W, height=ART_H, fill=f"url(#{k}-glow)"),
    ]


def mini(id_, x, y, fill, w=70, h=98, turn=0):
    """A small face-up card: body, white rim, a darker name band and a lighter art window."""
    return el(
        "g",
        id_,
        [
            el(
                "rect",
                f"{id_}-body",
                x=x,
                y=y,
                width=w,
                height=h,
                rx=7,
                fill=fill,
                stroke=WHITE,
                stroke_width=4,
            ),
            el(
                "rect",
                f"{id_}-band",
                x=x + 7,
                y=y + 7,
                width=w - 14,
                height=13,
                rx=2.5,
                fill=SHADE[fill],
            ),
            el(
                "rect",
                f"{id_}-art",
                x=x + 7,
                y=y + 25,
                width=w - 14,
                height=round(h * 0.36),
                rx=2.5,
                fill=LIGHT[fill],
            ),
        ],
        transform=f"rotate({num(turn)} {num(x + w / 2)} {num(y + h / 2)})",
    )


TURNS = [-3, 2, -1.5, 2.5, 0]


def pile(k, tag, cx, base, fill, n=5, w=70, h=98, step=6):
    return [
        mini(f"{k}-{tag}{i + 1}", cx - w / 2, base - h - i * step, fill, w, h, TURNS[i % 5])
        for i in range(n)
    ]


def back(id_, x, y, w=50, h=70, **attrs):
    """A small face-down card in the site's card-back colours."""
    return el(
        "g",
        id_,
        [
            el(
                "rect",
                f"{id_}-body",
                x=x,
                y=y,
                width=w,
                height=h,
                rx=5,
                fill="#111833",
                stroke=WHITE,
                stroke_width=3.5,
            ),
            el(
                "rect",
                f"{id_}-rim",
                x=x + 6,
                y=y + 6,
                width=w - 12,
                height=h - 12,
                rx=3,
                fill="none",
                stroke="#3D4F8F",
                stroke_width=2,
            ),
            el(
                "circle",
                f"{id_}-ring",
                cx=x + w / 2,
                cy=y + h / 2,
                r=w * 0.24,
                fill="none",
                stroke="#4A5FB0",
                stroke_width=2.5,
            ),
        ],
        **attrs,
    )


def disc(id_, cx, cy, r, fill, glyph):
    """A type disc holding one of the Energy glyphs from the 24-unit sprite grid."""
    return el(
        "g",
        id_,
        [
            el(
                "circle",
                f"{id_}-disc",
                cx=cx,
                cy=cy,
                r=r,
                fill=fill,
                stroke=WHITE,
                stroke_width=max(3, r / 12),
            ),
            el(
                "g",
                f"{id_}-glyph",
                glyph(id_),
                transform=f"translate({num(cx)} {num(cy)}) scale({num(r / 11)}) translate(-12 -12)",
            ),
        ],
    )


def psychic(id_):
    return [
        el(
            "circle",
            f"{id_}-glyph-ring",
            cx=12,
            cy=12,
            r=6.2,
            fill="none",
            stroke=WHITE,
            stroke_width=2,
        ),
        el("path", f"{id_}-glyph-core", d="M12 9.2L14.8 12L12 14.8L9.2 12Z", fill=WHITE),
    ]


def colorless(id_):
    return [
        el(
            "path",
            f"{id_}-glyph-hex",
            d="M12 6.2L17 9.1V14.9L12 17.8L7 14.9V9.1Z",
            fill="none",
            stroke=WHITE,
            stroke_width=2,
            stroke_linejoin="round",
        )
    ]


def gear_d(cx, cy, R, r, n=8):
    step = 2 * math.pi / n
    pts = []
    for i in range(n):
        a = i * step
        for rad, off in ((r, -0.3), (R, -0.17), (R, 0.17), (r, 0.3)):
            pts.append((cx + rad * math.cos(a + off * step), cy + rad * math.sin(a + off * step)))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


ART = {
    "training": (
        "#2E3C6A",
        "#161C33",
        "Training: two equal piles of five cards, blue and red, with an equals sign between them",
    ),
    "deck": (
        "#3A2470",
        "#140E2A",
        "Deck: a Psychic type disc and a Colorless type disc meeting at a gold spark",
    ),
    "training-and-deck": (
        "#1D4A5C",
        "#0B1D26",
        "Training and deck: four piles, blue and red under each deck's type, the taller pile swapping sides",
    ),
    "opponent": (
        "#5A1E28",
        "#1E0A0F",
        "Opponent: three tokens, a gear for the heuristic player, an arrow at the first option, a coin for random play",
    ),
    "seat": (
        "#1F4A3A",
        "#0A1A14",
        "Seat: a table seen from above with a blue chair and a red chair, and arrows for the seats swapping",
    ),
    "ending": (
        "#174A4E",
        "#0A1C1F",
        "Ending: six Prize card slots, five empty, the last card still face down",
    ),
    "checkpoint": (
        "#2A2F66",
        "#12142E",
        "Training run: six checkpoint flags along a track, three blue and three red",
    ),
    "matchup": (
        "#2B3550",
        "#121722",
        "Matchup grid: six rows of six cells, one row per checkpoint",
    ),
}


def motif(k):
    if k == "training":
        return [
            *pile(k, "fixed", 290, 232, BLUE),
            *pile(k, "diverse", 440, 232, RED),
            el(
                "g",
                f"{k}-equal",
                [
                    el("rect", f"{k}-equal-top", x=348, y=148, width=34, height=8, rx=4, fill=GOLD),
                    el(
                        "rect",
                        f"{k}-equal-bottom",
                        x=348,
                        y=164,
                        width=34,
                        height=8,
                        rx=4,
                        fill=GOLD,
                    ),
                ],
            ),
        ]
    if k == "deck":
        spark = "M370 116L379 141L404 150L379 159L370 184L361 159L336 150L361 141Z"
        return [
            disc(f"{k}-psychic", 292, 150, 66, "#6E44D6", psychic),
            disc(f"{k}-colorless", 448, 150, 66, "#6F7890", colorless),
            el(
                "path",
                f"{k}-spark",
                d=spark,
                fill=GOLD,
                stroke=WHITE,
                stroke_width=3,
                stroke_linejoin="round",
            ),
        ]
    if k == "training-and-deck":
        out = [
            disc(f"{k}-psychic", 360, 34, 20, "#6E44D6", psychic),
            disc(f"{k}-colorless", 470, 34, 20, "#6F7890", colorless),
        ]
        # Mewtwo: diverse ahead; Snorlax: fixed ahead
        for col, (cx, fixed, diverse) in enumerate(((360, 2, 6), (470, 6, 2))):
            out += pile(k, f"c{col + 1}fixed", cx, 162, BLUE, n=fixed, w=46, h=64, step=7)
            out += pile(k, f"c{col + 1}diverse", cx, 284, RED, n=diverse, w=46, h=64, step=7)
        return out
    if k == "opponent":
        y, r = 128, 48
        bars = [
            el(
                "rect",
                f"{k}-first-bar{i + 1}",
                x=366,
                y=y - 26 + i * 19,
                width=26,
                height=13,
                rx=3,
                fill=WHITE if i == 0 else "#8A4650",
            )
            for i in range(3)
        ]
        return [
            el(
                "g",
                f"{k}-heuristic",
                [
                    el(
                        "circle",
                        f"{k}-heuristic-disc",
                        cx=240,
                        cy=y,
                        r=r,
                        fill="#2F3B55",
                        stroke=WHITE,
                        stroke_width=4,
                    ),
                    el("path", f"{k}-heuristic-gear", d=gear_d(240, y, 30, 22), fill=GOLD),
                    el("circle", f"{k}-heuristic-hub", cx=240, cy=y, r=9, fill="#2F3B55"),
                ],
            ),
            el(
                "g",
                f"{k}-first",
                [
                    el(
                        "circle",
                        f"{k}-first-disc",
                        cx=357,
                        cy=y,
                        r=r,
                        fill="#2F3B55",
                        stroke=WHITE,
                        stroke_width=4,
                    ),
                    *bars,
                    el(
                        "path",
                        f"{k}-first-arrow",
                        d=f"M330 {y - 31}L346 {y - 19.5}L330 {y - 8}",
                        fill="none",
                        stroke=GOLD,
                        stroke_width=6,
                        stroke_linecap="round",
                        stroke_linejoin="round",
                    ),
                ],
            ),
            el(
                "g",
                f"{k}-coin",
                [
                    el(
                        "circle",
                        f"{k}-coin-disc",
                        cx=474,
                        cy=y,
                        r=r,
                        fill="#F2B531",
                        stroke=WHITE,
                        stroke_width=4,
                    ),
                    el(
                        "circle",
                        f"{k}-coin-rim",
                        cx=474,
                        cy=y,
                        r=38,
                        fill="none",
                        stroke="#B57F0E",
                        stroke_width=4,
                    ),
                    el(
                        "rect",
                        f"{k}-coin-card-left",
                        x=454,
                        y=110,
                        width=18,
                        height=26,
                        rx=3,
                        fill="none",
                        stroke="#6B4A06",
                        stroke_width=4,
                        transform="rotate(-5 463 123)",
                    ),
                    el(
                        "rect",
                        f"{k}-coin-card-right",
                        x=477,
                        y=110,
                        width=18,
                        height=26,
                        rx=3,
                        fill="#6B4A06",
                        transform="rotate(4 486 123)",
                    ),
                ],
            ),
        ]
    if k == "seat":

        def chair(id_, x, fill, flip):
            back_x = x + 34 if flip else x - 12
            return el(
                "g",
                id_,
                [
                    el(
                        "rect",
                        f"{id_}-back",
                        x=back_x,
                        y=118,
                        width=12,
                        height=64,
                        rx=5,
                        fill=SHADE[fill],
                        stroke=WHITE,
                        stroke_width=3,
                    ),
                    el(
                        "rect",
                        f"{id_}-seat",
                        x=x,
                        y=124,
                        width=34,
                        height=52,
                        rx=7,
                        fill=fill,
                        stroke=WHITE,
                        stroke_width=3.5,
                    ),
                ],
            )

        return [
            el(
                "rect",
                f"{k}-table",
                x=300,
                y=92,
                width=170,
                height=116,
                rx=18,
                fill="#1F6B4A",
                stroke="#0F3A28",
                stroke_width=6,
            ),
            mini(f"{k}-card-left", 318, 126, BLUE, w=34, h=48),
            mini(f"{k}-card-right", 418, 126, RED, w=34, h=48),
            chair(f"{k}-chair-left", 256, BLUE, False),
            chair(f"{k}-chair-right", 480, RED, True),
            el(
                "g",
                f"{k}-swap",
                [
                    el(
                        "path",
                        f"{k}-swap-top",
                        d="M290 72Q385 22 470 64",
                        fill="none",
                        stroke=GOLD,
                        stroke_width=6,
                        stroke_linecap="round",
                    ),
                    el(
                        "path",
                        f"{k}-swap-top-head",
                        d="M456 50L474 66L451 72",
                        fill="none",
                        stroke=GOLD,
                        stroke_width=6,
                        stroke_linecap="round",
                        stroke_linejoin="round",
                    ),
                    el(
                        "path",
                        f"{k}-swap-bottom",
                        d="M480 228Q385 278 300 236",
                        fill="none",
                        stroke=GOLD,
                        stroke_width=6,
                        stroke_linecap="round",
                    ),
                    el(
                        "path",
                        f"{k}-swap-bottom-head",
                        d="M314 250L296 234L319 228",
                        fill="none",
                        stroke=GOLD,
                        stroke_width=6,
                        stroke_linecap="round",
                        stroke_linejoin="round",
                    ),
                ],
            ),
        ]
    if k == "ending":
        out = []
        for i in range(6):
            x, y = 360 + (i % 2) * 66, 30 + (i // 2) * 88
            out.append(
                el(
                    "rect",
                    f"{k}-slot{i + 1}",
                    x=x,
                    y=y,
                    width=54,
                    height=76,
                    rx=6,
                    fill="#FFFFFF",
                    fill_opacity=0.06,
                    stroke="#7FB8B8",
                    stroke_opacity=0.55,
                    stroke_width=2.5,
                )
            )
        # Five Prize cards already taken (drawn hidden; the motion takes them), the last one left
        for i in range(5):
            x, y = 362 + (i % 2) * 66, 32 + (i // 2) * 88
            out.append(back(f"{k}-taken{i + 1}", x, y, opacity=0))
        out.append(
            el(
                "rect",
                f"{k}-last-glow",
                x=418,
                y=200,
                width=66,
                height=88,
                rx=10,
                fill="none",
                stroke=GOLD,
                stroke_width=4,
            )
        )
        out.append(back(f"{k}-last", 428, 208))
        return out
    if k == "checkpoint":
        out = [el("rect", f"{k}-track", x=226, y=196, width=282, height=10, rx=5, fill="#3D4F8F")]
        for i, x in enumerate((246, 290, 334, 400, 444, 488)):
            fill = BLUE if i < 3 else RED
            out.append(
                el(
                    "g",
                    f"{k}-flag{i + 1}",
                    [
                        el(
                            "rect",
                            f"{k}-flag{i + 1}-pole",
                            x=x - 2.5,
                            y=96,
                            width=5,
                            height=106,
                            rx=2.5,
                            fill=WHITE,
                        ),
                        el(
                            "path",
                            f"{k}-flag{i + 1}-cloth",
                            d=f"M{x + 2} 98L{x + 36} 113L{x + 2} 128Z",
                            fill=fill,
                            stroke=WHITE,
                            stroke_width=3,
                            stroke_linejoin="round",
                        ),
                        el(
                            "circle",
                            f"{k}-flag{i + 1}-base",
                            cx=x,
                            cy=201,
                            r=9,
                            fill=fill,
                            stroke=WHITE,
                            stroke_width=3,
                        ),
                    ],
                )
            )
        return out
    if k == "matchup":
        shades = {"C": "#3AD6F7", "M": "#2A9FC0", "D": "#1D6F8A", "G": GOLD}
        pattern = ["CMGDCM", "DCMDMC", "MDCGMD", "CMDCDG", "GDMCMC", "MCDMGD"]
        out = []
        for row in range(6):
            out.append(
                el(
                    "circle",
                    f"{k}-row{row + 1}",
                    cx=318,
                    cy=50 + row * 36,
                    r=8,
                    fill=BLUE if row < 3 else RED,
                    stroke=WHITE,
                    stroke_width=2.5,
                )
            )
            for col in range(6):
                out.append(
                    el(
                        "rect",
                        f"{k}-cell{row + 1}-{col + 1}",
                        x=342 + col * 32,
                        y=37 + row * 36,
                        width=26,
                        height=26,
                        rx=5,
                        fill=shades[pattern[row][col]],
                    )
                )
        return out
    raise KeyError(k)


def sort_art(k):
    inner, outer, title = ART[k]
    return [
        el("title", f"{k}-title", text=title),
        *ground(k, inner, outer),
        el("g", f"{k}-motif", motif(k)),
    ]


SORT_ART = list(ART)


# Pokemon art: six original abstract motifs for the art window of Pokemon cards on the replay
# board, one per card name. White on a placeholder ground; the site's sprite drops the ground,
# draws the white in currentColor and lets CSS colour the window by type. No likenesses.
MON_ART = 6


def star4(cx, cy, r, w):
    return f"M{num(cx)} {num(cy - r)}L{num(cx + w)} {num(cy - w)}L{num(cx + r)} {num(cy)}L{num(cx + w)} {num(cy + w)}L{num(cx)} {num(cy + r)}L{num(cx - w)} {num(cy + w)}L{num(cx - r)} {num(cy)}L{num(cx - w)} {num(cy - w)}Z"


def mon_motif(i):
    k = f"mon-art-{i}"
    if i == 1:  # burst: an orb throwing rays
        rays = ""
        for j in range(16):
            a0, a1 = math.radians(j * 22.5 - 4), math.radians(j * 22.5 + 4)
            rays += f"M{271 + 84 * math.cos(a0):.1f} {166 + 84 * math.sin(a0):.1f}L{271 + 230 * math.cos((a0 + a1) / 2):.1f} {166 + 230 * math.sin((a0 + a1) / 2):.1f}L{271 + 84 * math.cos(a1):.1f} {166 + 84 * math.sin(a1):.1f}Z"
        return [
            el("path", f"{k}-rays", d=rays, fill=WHITE, fill_opacity=0.16),
            el(
                "circle",
                f"{k}-ring",
                cx=271,
                cy=166,
                r=78,
                fill="none",
                stroke=WHITE,
                stroke_opacity=0.45,
                stroke_width=6,
            ),
            el("circle", f"{k}-orb", cx=271, cy=166, r=56, fill=WHITE, fill_opacity=0.85),
        ]
    if i == 2:  # orbit: a planet with a ring and two moons
        return [
            *[
                el(
                    "path",
                    f"{k}-star{j + 1}",
                    d=star4(x, y, r, r / 4),
                    fill=WHITE,
                    fill_opacity=0.7,
                )
                for j, (x, y, r) in enumerate(
                    ((70, 60, 12), (480, 70, 9), (440, 270, 11), (110, 260, 8))
                )
            ],
            el("circle", f"{k}-planet", cx=271, cy=170, r=72, fill=WHITE, fill_opacity=0.8),
            el(
                "ellipse",
                f"{k}-ring",
                cx=271,
                cy=170,
                rx=150,
                ry=34,
                fill="none",
                stroke=WHITE,
                stroke_opacity=0.55,
                stroke_width=9,
                transform="rotate(-16 271 170)",
            ),
            el("circle", f"{k}-moon1", cx=420, cy=104, r=14, fill=WHITE, fill_opacity=0.85),
            el("circle", f"{k}-moon2", cx=128, cy=226, r=8, fill=WHITE, fill_opacity=0.7),
        ]
    if i == 3:  # peaks: layered mountains under a sun
        return [
            el("circle", f"{k}-sun", cx=380, cy=96, r=44, fill=WHITE, fill_opacity=0.85),
            el(
                "path",
                f"{k}-back",
                d="M0 332L0 230L90 140L170 210L270 100L380 220L460 160L542 230L542 332Z",
                fill=WHITE,
                fill_opacity=0.22,
            ),
            el(
                "path",
                f"{k}-front",
                d="M0 332L0 280L120 190L210 260L320 170L430 270L542 220L542 332Z",
                fill=WHITE,
                fill_opacity=0.5,
            ),
        ]
    if i == 4:  # swirl: a spiral with sparkles
        pts = []
        for j in range(0, 721, 12):
            a = math.radians(j)
            r = 8 + j * 0.16
            pts.append((271 + r * math.cos(a), 166 + r * math.sin(a) * 0.82))
        spiral = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        return [
            el(
                "path",
                f"{k}-spiral",
                d=spiral,
                fill="none",
                stroke=WHITE,
                stroke_opacity=0.6,
                stroke_width=12,
                stroke_linecap="round",
                stroke_linejoin="round",
            ),
            el("circle", f"{k}-eye", cx=271, cy=166, r=14, fill=WHITE, fill_opacity=0.9),
            *[
                el(
                    "path",
                    f"{k}-spark{j + 1}",
                    d=star4(x, y, r, r / 4),
                    fill=WHITE,
                    fill_opacity=0.8,
                )
                for j, (x, y, r) in enumerate(
                    ((90, 80, 16), (460, 90, 13), (470, 250, 18), (80, 250, 11))
                )
            ],
        ]
    if i == 5:  # bolts: three zigzags of energy
        out = []
        for j, (y, op, w) in enumerate(((96, 0.35, 8), (166, 0.85, 14), (236, 0.35, 8))):
            d = f"M30 {y}" + "".join(
                f"L{30 + (n + 1) * 60} {y + (-28 if n % 2 == 0 else 28)}" for n in range(8)
            )
            out.append(
                el(
                    "path",
                    f"{k}-bolt{j + 1}",
                    d=d,
                    fill="none",
                    stroke=WHITE,
                    stroke_opacity=op,
                    stroke_width=w,
                    stroke_linecap="round",
                    stroke_linejoin="round",
                )
            )
        return out
    if i == 6:  # bubbles: rising circles
        out = []
        for j, (x, y, r, filled) in enumerate(
            (
                (120, 230, 46, 1),
                (220, 120, 30, 0),
                (300, 220, 62, 0),
                (400, 110, 40, 1),
                (470, 230, 24, 1),
                (60, 110, 18, 0),
                (350, 60, 14, 1),
                (200, 280, 12, 1),
                (510, 70, 10, 0),
            )
        ):
            out.append(
                el(
                    "circle",
                    f"{k}-b{j + 1}",
                    cx=x,
                    cy=y,
                    r=r,
                    fill=WHITE if filled else "none",
                    fill_opacity=0.5 if filled else 1,
                    stroke=WHITE,
                    stroke_opacity=0.7,
                    stroke_width=5,
                )
            )
        return out
    raise KeyError(i)


def mon_art_svg(i):
    k = f"mon-art-{i}"
    titles = {
        1: "an orb throwing rays",
        2: "a ringed planet with two moons",
        3: "layered mountains under a sun",
        4: "a spiral with sparkles",
        5: "three zigzags of energy",
        6: "rising bubbles",
    }
    els = [
        el("title", f"{k}-title", text=f"Pokemon card art {i}: {titles[i]}"),
        el("rect", f"{k}-ground", x=0, y=0, width=ART_W, height=ART_H, fill="#3E4658"),
        el("g", f"{k}-motif", mon_motif(i)),
    ]
    body = "".join(serialize(e) for e in els)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{ART_W}" height="{ART_H}" viewBox="0 0 {ART_W} {ART_H}">{body}</svg>\n'


def serialize(e):
    if "text" in e:
        return f'<{e["type"]} id="{e["id"]}">{escape(e["text"], quote=False)}</{e["type"]}>'
    attrs = "".join(f' {k}="{escape(v)}"' for k, v in e["attributes"].items())
    if "children" in e:
        return (
            f'<{e["type"]} id="{e["id"]}"{attrs}>'
            + "".join(serialize(c) for c in e["children"])
            + f"</{e['type']}>"
        )
    return f'<{e["type"]} id="{e["id"]}"{attrs} />'


def svg(face):
    body = "".join(
        serialize(e) for e in (energy_elements(face) if face in ENERGY else elements(face))
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="630" height="880" viewBox="0 0 630 880">{body}</svg>\n'


def art_svg(k):
    body = "".join(serialize(e) for e in sort_art(k))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{ART_W}" height="{ART_H}" viewBox="0 0 {ART_W} {ART_H}">{body}</svg>\n'


if __name__ == "__main__":
    if sys.argv[1] == "elements":
        f = sys.argv[2]
        print(
            json.dumps(
                energy_elements(f) if f in ENERGY else sort_art(f) if f in SORT_ART else elements(f)
            )
        )
    elif sys.argv[1] == "art":
        for k in SORT_ART:
            (HERE / f"sort-{k}.svg").write_text(art_svg(k))
        for i in range(1, MON_ART + 1):
            (HERE / f"mon-art-{i}.svg").write_text(mon_art_svg(i))
    else:
        for face in [*TYPES, *ENERGY]:
            (HERE / f"face-{face}.svg").write_text(svg(face))
