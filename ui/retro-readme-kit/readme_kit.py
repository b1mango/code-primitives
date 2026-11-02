#!/usr/bin/env python3
"""Retro README Kit: generate a hardware-panel style README asset set.

Every visual piece of the README (hero, section headers, keycap links,
language switch) is a self-contained SVG rendered twice (day / night) and
wired into Markdown with <picture> + prefers-color-scheme. English labels are
drawn with a built-in pixel font converted to <path>, so they look identical
on every machine without any web font.

Zero dependencies (Python 3.8+ stdlib only).

Usage:
    python3 readme_kit.py readme-kit.json                  # write SVG assets
    python3 readme_kit.py readme-kit.json --template README.template.md --readme README.md
    python3 readme_kit.py readme-kit.json --preview preview.html --gallery themes/
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

MODES = ("day", "night")
WIDTH = 860
CJK_FONT = '"PingFang SC","Microsoft YaHei UI","Noto Sans SC","Microsoft YaHei",sans-serif'

# ---------------------------------------------------------------------------
# Pixel font: 7 rows tall, variable width, 2-cell vertical stems.
# ---------------------------------------------------------------------------

_FONT_SRC = {
    "A": ".####. ##..## ##..## ###### ##..## ##..## ##..##",
    "B": "#####. ##..## ##..## #####. ##..## ##..## #####.",
    "C": ".####. ##..## ##.... ##.... ##.... ##..## .####.",
    "D": "####.. ##.##. ##..## ##..## ##..## ##.##. ####..",
    "E": "###### ##.... ##.... #####. ##.... ##.... ######",
    "F": "###### ##.... ##.... #####. ##.... ##.... ##....",
    "G": ".####. ##..## ##.... ##.### ##..## ##..## .#####",
    "H": "##..## ##..## ##..## ###### ##..## ##..## ##..##",
    "I": "#### .##. .##. .##. .##. .##. ####",
    "J": "....## ....## ....## ....## ##..## ##..## .####.",
    "K": "##..## ##.##. ####.. ###... ####.. ##.##. ##..##",
    "L": "##.... ##.... ##.... ##.... ##.... ##.... ######",
    "M": "##...## ###.### ####### ##.#.## ##...## ##...## ##...##",
    "N": "##...## ###..## ####.## ##.#### ##..### ##...## ##...##",
    "O": ".####. ##..## ##..## ##..## ##..## ##..## .####.",
    "P": "#####. ##..## ##..## #####. ##.... ##.... ##....",
    "Q": ".####. ##..## ##..## ##..## ##..## ##.##. .##.##",
    "R": "#####. ##..## ##..## #####. ####.. ##.##. ##..##",
    "S": ".##### ##.... ##.... .####. ....## ....## #####.",
    "T": "###### ..##.. ..##.. ..##.. ..##.. ..##.. ..##..",
    "U": "##..## ##..## ##..## ##..## ##..## ##..## .####.",
    "V": "##..## ##..## ##..## ##..## ##..## .####. ..##..",
    "W": "##...## ##...## ##...## ##.#.## ####### ###.### ##...##",
    "X": "##..## ##..## .####. ..##.. .####. ##..## ##..##",
    "Y": "##..## ##..## ##..## .####. ..##.. ..##.. ..##..",
    "Z": "###### ....## ...##. ..##.. .##... ##.... ######",
    "0": ".####. ##..## ##.### ###### ###.## ##..## .####.",
    "1": "..##.. .###.. ..##.. ..##.. ..##.. ..##.. ######",
    "2": ".####. ##..## ....## ..###. .##... ##.... ######",
    "3": "#####. ....## ....## .####. ....## ....## #####.",
    "4": "...### ..#### .##.## ##..## ###### ....## ....##",
    "5": "###### ##.... #####. ....## ....## ##..## .####.",
    "6": ".####. ##.... ##.... #####. ##..## ##..## .####.",
    "7": "###### ....## ...##. ..##.. ..##.. ..##.. ..##..",
    "8": ".####. ##..## ##..## .####. ##..## ##..## .####.",
    "9": ".####. ##..## ##..## .##### ....## ...##. .###..",
    " ": "... ... ... ... ... ... ...",
    ".": ".. .. .. .. .. ## ##",
    ",": ".. .. .. .. .. ## .#",
    ":": ".. ## ## .. ## ## ..",
    "-": ".... .... .... #### .... .... ....",
    "_": "###### ...... ...... ...... ...... ...... ......",  # flipped below
    "+": "...... ..##.. ..##.. ###### ..##.. ..##.. ......",
    "/": "....## ....## ...##. ..##.. .##... ##.... ##....",
    "!": "## ## ## ## ## .. ##",
    "?": ".####. ##..## ....## ..###. ..##.. ...... ..##..",
    "'": "## ## .. .. .. .. ..",
    "(": ".## ##. ##. ##. ##. ##. .##",
    ")": "##. .## .## .## .## .## ##.",
    "<": "...## ..##. .##.. ##... .##.. ..##. ...##",
    ">": "##... .##.. ..##. ...## ..##. .##.. ##...",
    "|": "## ## ## ## ## ## ##",
    "#": ".##.##. ####### .##.##. .##.##. ####### .##.##. .......",
    "*": "...... ##..## .####. ###### .####. ##..## ......",
    "&": ".###.. ##.##. .###.. ###.## ##.##. ##..## .###.#",
    "·": ".. .. .. ## .. .. ..",
}


def _build_font(src: dict) -> dict:
    font = {}
    for ch, rows in src.items():
        glyph = rows.split()
        if ch == "_":
            glyph = glyph[::-1]
        font[ch] = tuple(glyph)
    return font


FONT = _build_font(_FONT_SRC)
TRACKING = 1  # empty cells between glyphs


def _num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _glyph(ch: str):
    ch = ch.upper()
    return FONT.get(ch, FONT["?"])


def pixel_width(text: str, cell: float, tracking: int = TRACKING) -> float:
    """Rendered width of `text` in the pixel font at `cell` px per cell."""
    if not text:
        return 0.0
    units = sum(len(_glyph(c)[0]) for c in text) + tracking * (len(text) - 1)
    return units * cell


def pixel_path(text: str, x: float, y: float, cell: float, tracking: int = TRACKING) -> str:
    """Return path data drawing `text` with its top-left corner at (x, y).

    Each horizontal run of lit cells becomes one rectangle sub-path, which
    keeps the output compact and crisp at any scale.
    """
    parts = []
    cx = x
    for ch in text:
        glyph = _glyph(ch)
        for r, row in enumerate(glyph):
            c = 0
            while c < len(row):
                if row[c] != "#":
                    c += 1
                    continue
                start = c
                while c < len(row) and row[c] == "#":
                    c += 1
                w = (c - start) * cell
                parts.append(f"M{_num(cx + start * cell)} {_num(y + r * cell)}h{_num(w)}v{_num(cell)}h{_num(-w)}z")
        cx += (len(glyph[0]) + tracking) * cell
    return "".join(parts)


def pixel_text(text: str, x: float, y: float, cell: float, fill: str, extra: str = "") -> str:
    d = pixel_path(text, x, y, cell)
    if not d:
        return ""
    return f'<path d="{d}" fill="{fill}" shape-rendering="crispEdges"{extra}/>'


def text_width(text: str, size: float) -> float:
    """Rough width estimate for system-font <text> (bold CJK UI fonts)."""
    w = 0.0
    for ch in text:
        o = ord(ch)
        if o >= 0x2E80 or ch in "，。：；！？、（）《》【】“”":
            w += 1.0
        elif ch == " ":
            w += 0.3
        elif ch.isupper() or ch.isdigit():
            w += 0.64
        elif ch in "il.,:;'|!":
            w += 0.3
        else:
            w += 0.56
    return w * size


# ---------------------------------------------------------------------------
# Themes. Every theme has a day and a night palette plus three LED colours.
# ---------------------------------------------------------------------------

THEMES = {
    "beige": {
        "leds": ["#8fd6a0", "#ffd84a", "#f08a5d"],
        "day": dict(shell="#ddd4bf", hi="#f6f1e3", lo="#bdb39c", shadow="#9c927b", line="#5a544a",
                    ink="#4a443a", ink_soft="#6b6455", vent="#a89e87", screen="#f4efe2",
                    grain="rgba(0,0,0,.05)", plate="#5a544a", plate_ink="#f3eee1", key="#f3eee1",
                    key_shadow="#c2b8a1", key_hi="#fffaf0", accent="#f08a5d", accent_shadow="#c2643c",
                    accent_ink="#3a2a22"),
        "night": dict(shell="#2f2c28", hi="#4a453f", lo="#24221f", shadow="#1d1b18", line="#171513",
                      ink="#ebe4d2", ink_soft="#b8b0a0", vent="#1d1b18", screen="#26231f",
                      grain="rgba(255,255,255,.04)", plate="#ebe4d2", plate_ink="#2f2c28", key="#3a3631",
                      key_shadow="#1d1b18", key_hi="#4f4a43", accent="#f08a5d", accent_shadow="#a8502c",
                      accent_ink="#2a1c14"),
    },
    "mint": {
        "leds": ["#7bc96f", "#f2d45c", "#e86f6f"],
        "day": dict(shell="#cfe0d0", hi="#eef6ee", lo="#a9c2ab", shadow="#86a088", line="#2f4a3a",
                    ink="#24392c", ink_soft="#4d6a57", vent="#97b29a", screen="#e3efd9",
                    grain="rgba(0,0,0,.05)", plate="#2f4a3a", plate_ink="#e6f2e4", key="#eef6ee",
                    key_shadow="#a9c2ab", key_hi="#ffffff", accent="#7bc96f", accent_shadow="#4f9a45",
                    accent_ink="#16301a"),
        "night": dict(shell="#1f2b24", hi="#33453a", lo="#18221c", shadow="#111813", line="#0b100d",
                      ink="#d8ecd9", ink_soft="#9db8a2", vent="#141c17", screen="#16201a",
                      grain="rgba(255,255,255,.04)", plate="#d8ecd9", plate_ink="#1f2b24", key="#2a3a30",
                      key_shadow="#111813", key_hi="#3b5143", accent="#7bc96f", accent_shadow="#3f7a37",
                      accent_ink="#0f2412"),
    },
    "slate": {
        "leds": ["#5ad1c4", "#ffcf5a", "#ff7a8a"],
        "day": dict(shell="#d9dde6", hi="#f4f6fa", lo="#b5bccb", shadow="#959db0", line="#3b4256",
                    ink="#2c3244", ink_soft="#5a6278", vent="#a6aec0", screen="#eef1f7",
                    grain="rgba(0,0,0,.05)", plate="#3b4256", plate_ink="#eef1f7", key="#f4f6fa",
                    key_shadow="#b5bccb", key_hi="#ffffff", accent="#6c8cff", accent_shadow="#4462d6",
                    accent_ink="#101a3d"),
        "night": dict(shell="#252a36", hi="#3a4152", lo="#1e222c", shadow="#14171f", line="#0c0e13",
                      ink="#e3e7f0", ink_soft="#a3abbd", vent="#181b23", screen="#1b1f28",
                      grain="rgba(255,255,255,.04)", plate="#e3e7f0", plate_ink="#252a36", key="#2f3544",
                      key_shadow="#14171f", key_hi="#424a5d", accent="#6c8cff", accent_shadow="#3a52b0",
                      accent_ink="#0b1230"),
    },
}


def palette(theme: str, mode: str) -> dict:
    if theme not in THEMES:
        raise ValueError(f"unknown theme {theme!r}; choose one of {sorted(THEMES)}")
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    p = dict(THEMES[theme][mode])
    p["leds"] = THEMES[theme]["leds"]
    return p


# ---------------------------------------------------------------------------
# SVG building blocks
# ---------------------------------------------------------------------------

def _attr(s: str) -> str:
    return escape(s, {'"': "&quot;"})


def _svg(w: float, h: float, label: str, body: str, defs: str = "", fixed_width: bool = True) -> str:
    size = f' width="{_num(w)}" height="{_num(h)}"' if fixed_width else f' width="{_num(w)}"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_num(w)} {_num(h)}"{size} '
        f'role="img" aria-label="{_attr(label)}"><title>{escape(label)}</title>'
        f"<defs><style>.c{{font-family:{CJK_FONT};font-weight:700}}</style>{defs}</defs>"
        f"{body}</svg>\n"
    )


def _bevel_box(x, y, w, h, p, face=None, drop=4) -> str:
    """Chassis-style box: hard drop shadow, outline, top-left highlight, bottom-right shade."""
    face = face or p["shell"]
    return (
        f'<rect x="{x}" y="{y + drop}" width="{w}" height="{h}" fill="{p["shadow"]}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{face}" stroke="{p["line"]}" stroke-width="2"/>'
        f'<path d="M{x + 3} {y + h - 2}V{y + 3}H{x + w - 3}" fill="none" stroke="{p["hi"]}" stroke-width="2"/>'
        f'<path d="M{x + w - 3} {y + 3}V{y + h - 3}H{x + 3}" fill="none" stroke="{p["lo"]}" stroke-width="2"/>'
    )


def _vent_def(p, h=20) -> str:
    return (f'<pattern id="vent" width="6" height="{h}" patternUnits="userSpaceOnUse">'
            f'<rect width="2" height="{h}" fill="{p["vent"]}"/></pattern>')


def _led(x, y, color, p, size=11) -> str:
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{color}" stroke="{p["line"]}" stroke-width="1.2"/>'


def section_svg(en: str, zh: str, index: int, p: dict) -> str:
    """Full-width section header: dark plate with pixel EN title, CJK title, vent grille, index + LED."""
    h = 46
    cell = 2
    en_w = pixel_width(en, cell)
    plate_w = round(en_w + 30)
    zh_x = plate_w + 14
    zh_w = text_width(zh, 16)
    idx = f"{index:02d}"
    idx_cell = 1.5
    idx_w = pixel_width(idx, idx_cell)
    led_x = WIDTH - 28
    idx_x = led_x - 12 - idx_w
    vent_x = round(zh_x + zh_w + 16)
    vent_w = max(0, round(idx_x - 14 - vent_x))
    body = (
        _bevel_box(1, 1, WIDTH - 2, 40, p)
        + f'<rect x="2" y="2" width="{plate_w}" height="38" fill="{p["plate"]}"/>'
        + pixel_text(en, 15, 14, cell, p["plate_ink"])
        + f'<text class="c" x="{zh_x}" y="27" font-size="16" fill="{p["ink"]}">{escape(zh)}</text>'
        + (f'<rect x="{vent_x}" y="11" width="{vent_w}" height="20" fill="url(#vent)" opacity=".85"/>' if vent_w > 8 else "")
        + pixel_text(idx, idx_x, 15.75, idx_cell, p["ink_soft"])
        + _led(led_x, 15, p["leds"][0], p)
    )
    return _svg(WIDTH, h, f"{zh} · {en}", body, _vent_def(p), fixed_width=False)


def keycap_svg(label: str, tag: str, p: dict, accent: bool = False) -> str:
    """Clickable-looking keycap. `label` is CJK/any text, `tag` an optional pixel-font suffix."""
    size = 14 if tag else 12
    pad = 15 if tag else 11
    lw = text_width(label, size)
    tag_cell = 1.5
    tw = pixel_width(tag, tag_cell) if tag else 0
    gap = 10 if tag else 0
    w = round(pad * 2 + lw + gap + tw)
    h = 36 if tag else 28
    face, shade, hi, ink = (
        (p["accent"], p["accent_shadow"], "rgba(255,255,255,.3)", p["accent_ink"]) if accent
        else (p["key"], p["key_shadow"], p["key_hi"], p["ink"])
    )
    body = (
        f'<rect x="1" y="5" width="{w}" height="{h}" fill="{shade}" stroke="{p["line"]}" stroke-width="2"/>'
        f'<rect x="1" y="1" width="{w}" height="{h}" fill="{face}" stroke="{p["line"]}" stroke-width="2"/>'
        f'<path d="M3 {h - 1}V3H{w - 1}" fill="none" stroke="{hi}" stroke-width="2"/>'
        f'<text class="c" x="{pad + 1}" y="{_num(1 + h / 2 + size * 0.36)}" font-size="{size}" fill="{ink}">{escape(label)}</text>'
    )
    if tag:
        body += pixel_text(tag, pad + 1 + lw + gap, 1 + h / 2 - 3.5 * tag_cell, tag_cell, ink, ' opacity=".75"')
    return _svg(w + 2, h + 7, label, body)


def _chip(x, y, text, p, filled) -> tuple:
    cell = 1.5
    tw = pixel_width(text, cell)
    w = round(tw + 20)
    if filled:
        out = f'<rect x="{x}" y="{y}" width="{w}" height="22" fill="{p["plate"]}"/>'
        ink = p["plate_ink"]
    else:
        out = f'<rect x="{x + 0.75}" y="{y + 0.75}" width="{w - 1.5}" height="20.5" fill="none" stroke="{p["line"]}" stroke-width="1.5"/>'
        ink = p["ink"]
    out += pixel_text(text, x + 10, y + 11 - 3.5 * cell, cell, ink)
    return out, w


def _resolve_color(value: str, p: dict) -> str:
    if value.startswith("$"):
        key = value[1:]
        if key.startswith("led") and key[3:].isdigit():
            return p["leds"][int(key[3:])]
        return p[key]
    return value


def sprite_svg(sprite: dict, x, y, max_w, max_h, p) -> str:
    rows = sprite["rows"]
    if not rows or len({len(r) for r in rows}) != 1:
        raise ValueError("sprite rows must be non-empty and equal length")
    colors = {k: _resolve_color(v, p) for k, v in sprite["palette"].items()}
    sw, sh = len(rows[0]), len(rows)
    scale = int(min(max_w / sw, max_h / sh))
    if scale < 1:
        raise ValueError("sprite too large for the hero window")
    ox = x + (max_w - sw * scale) / 2
    oy = y + (max_h - sh * scale) / 2
    runs = {}
    for r, row in enumerate(rows):
        c = 0
        while c < sw:
            k = row[c]
            start = c
            while c < sw and row[c] == k:
                c += 1
            if k in colors:
                runs.setdefault(k, []).append(
                    f"M{_num(ox + start * scale)} {_num(oy + r * scale)}h{(c - start) * scale}v{scale}h{-(c - start) * scale}z")
    return "".join(f'<path d="{"".join(d)}" fill="{colors[k]}" shape-rendering="crispEdges"/>' for k, d in runs.items())


TITLE_MAX_W = 480


def title_cell(title: str) -> float:
    """Largest half-pixel cell (max 10) that fits `title` in the hero panel."""
    cell = int(min(10.0, TITLE_MAX_W / max(1, pixel_width(title, 1))) * 2) / 2
    if cell < 3:
        raise ValueError(f"hero title {title!r} is too long; keep it to about 12 characters "
                         "and move the rest into 'tagline'")
    return cell


def hero_svg(cfg: dict, p: dict, base_dir: Path, animate: bool = True) -> str:
    hero = cfg.get("hero", {})
    name = cfg["name"]
    h = 340
    defs = (
        _vent_def(p, 18)
        + f'<pattern id="grain" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="1" height="1" fill="{p["grain"]}"/></pattern>'
        + f'<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="{p["grain"]}"/></pattern>'
        + '<clipPath id="win"><rect x="585" y="81" width="254" height="229"/></clipPath>'
    )
    b = [_bevel_box(1, 1, WIDTH - 2, h - 8, p, drop=6)]
    # title bar
    b.append(f'<line x1="2" y1="42" x2="{WIDTH - 2}" y2="42" stroke="{p["line"]}" stroke-width="2"/>')
    b.append(f'<g stroke="{p["line"]}" stroke-width="1.5">' + "".join(
        f'<rect x="{16 + i * 12}" y="12" width="12" height="20" fill="{c}"/>' for i, c in enumerate(p["leds"])) + "</g>")
    kicker = hero.get("kicker", f"{name} // README")
    b.append(pixel_text(kicker, 66, 15, 2, p["ink_soft"]))
    vent_x = round(66 + pixel_width(kicker, 2) + 18)
    b.append(f'<rect x="{vent_x}" y="13" width="{max(0, WIDTH - 50 - vent_x)}" height="18" fill="url(#vent)"/>')
    b.append(_led(WIDTH - 28, 16, p["leds"][0], p))

    # left screen
    b.append(f'<rect x="28" y="60" width="538" height="252" fill="{p["screen"]}" stroke="{p["line"]}" stroke-width="2"/>')
    b.append('<rect x="29" y="61" width="536" height="250" fill="url(#grain)"/>')
    y = 78
    b.append(f'<rect x="52" y="{y + 2}" width="10" height="10" fill="{p["accent"]}"/>')
    tx = 70
    if hero.get("name_zh"):
        b.append(f'<text class="c" x="{tx}" y="{y + 12}" font-size="14" fill="{p["ink"]}">{escape(hero["name_zh"])}</text>')
        tx += text_width(hero["name_zh"], 14) + 10
    if hero.get("name_tag"):
        b.append(pixel_text(hero["name_tag"], tx, y + 2, 1.5, p["ink_soft"]))

    title = hero.get("title", name)
    cell = title_cell(title)
    title_w = pixel_width(title, cell)
    ty = 104
    b.append(pixel_text(title, 52, ty, cell, p["ink"]))
    bar_y = ty + 7 * cell + 14
    bar_w = min(title_w, 336)
    segs = (0.56, 0.2, 0.24)
    sx = 52.0
    for frac, color in zip(segs, p["leds"]):
        b.append(f'<rect x="{_num(sx)}" y="{_num(bar_y)}" width="{_num(bar_w * frac)}" height="4" fill="{color}"/>')
        sx += bar_w * frac
    line_y = bar_y + 32
    if hero.get("tagline"):
        b.append(f'<text class="c" x="52" y="{_num(line_y)}" font-size="19" fill="{p["ink"]}">{escape(hero["tagline"])}</text>')
        line_y += 23
    if hero.get("subline"):
        b.append(f'<text class="c" x="52" y="{_num(line_y)}" font-size="12.5" fill="{p["ink_soft"]}">{escape(hero["subline"])}</text>')
    cx = 52
    for i, chip in enumerate(hero.get("chips", [])[:4]):
        out, w = _chip(cx, 276, chip, p, filled=(i == 0))
        b.append(out)
        cx += w + 8

    # right window: a tiny OS window with title strip
    b.append(f'<rect x="584" y="60" width="256" height="252" fill="{p["screen"]}" stroke="{p["line"]}" stroke-width="2"/>')
    b.append(f'<rect x="585" y="61" width="254" height="19" fill="{p["plate"]}"/>')
    b.append(pixel_text(hero.get("window_title", "PREVIEW.BMP"), 593, 65.5, 1.15, p["plate_ink"]))
    b.append("".join(f'<rect x="{804 + i * 11}" y="66" width="8" height="8" fill="none" stroke="{p["plate_ink"]}" stroke-width="1.2"/>' for i in range(3)))
    b.append(f'<line x1="585" y1="80" x2="839" y2="80" stroke="{p["line"]}" stroke-width="2"/>')
    if hero.get("image"):
        img_path = (base_dir / hero["image"]).resolve()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
                "webp": "image/webp", "svg": "image/svg+xml"}[img_path.suffix.lower().lstrip(".")]
        data = base64.b64encode(img_path.read_bytes()).decode()
        b.append(f'<g clip-path="url(#win)"><image href="data:{mime};base64,{data}" x="585" y="81" width="254" height="229" preserveAspectRatio="xMidYMid slice"/></g>')
    else:
        b.append('<rect x="585" y="81" width="254" height="229" fill="url(#grain)"/>')
        if hero.get("sprite"):
            b.append(sprite_svg(hero["sprite"], 600, 92, 224, 176, p))
        status = hero.get("status", "READY")
        sw = pixel_width(status, 2)
        sx = 712 - (sw + 16) / 2
        b.append(pixel_text(status, sx, 284, 2, p["ink"]))
        blink = ('<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" '
                 'repeatCount="indefinite"/>') if animate else ""
        b.append(f'<rect x="{_num(sx + sw + 4)}" y="284" width="10" height="14" fill="{p["accent"]}">{blink}</rect>')
        b.append('<rect x="585" y="81" width="254" height="229" fill="url(#scan)"/>')
    b.append(f'<rect x="584" y="60" width="256" height="252" fill="none" stroke="{p["line"]}" stroke-width="2"/>')
    label = f"{name}：{hero.get('tagline', '')}".rstrip("：")
    return _svg(WIDTH, h, label, "".join(b), defs, fixed_width=False)


# ---------------------------------------------------------------------------
# Markdown snippets
# ---------------------------------------------------------------------------

def picture(asset_dir: str, stem: str, alt: str, width: str = "") -> str:
    w = f' width="{width}"' if width else ""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{asset_dir}/{stem}-night.svg">'
            f'<img src="{asset_dir}/{stem}-day.svg" alt="{_attr(alt)}"{w}></picture>')


def _shield_escape(s: str) -> str:
    return quote(s.replace("-", "--").replace("_", "__"), safe="")


def badge_urls(cfg: dict, theme: str) -> list:
    p = palette(theme, "day")
    label_color = p["line"].lstrip("#")
    leds = [c.lstrip("#") for c in p["leds"]]
    repo = cfg.get("repo", "")
    out = []
    for i, b in enumerate(cfg.get("badges", [])):
        color = b.get("color", leds[i % len(leds)]).lstrip("#")
        style = f"style=flat-square&labelColor={label_color}"
        if "github" in b:
            if not repo:
                raise ValueError("github badges need a top-level 'repo' (owner/name)")
            kind = b["github"]
            label = quote(b.get("label", kind.replace("-", " ").title()))
            paths = {"stars": "stars", "forks": "forks", "license": "license", "contributors": "contributors",
                     "last-commit": "last-commit", "release": "v/release"}
            url = f"https://img.shields.io/github/{paths[kind]}/{repo}?label={label}&color={color}&{style}"
            alt = b.get("label", kind)
        else:
            url = (f"https://img.shields.io/badge/{_shield_escape(b['label'])}-{_shield_escape(b['message'])}"
                   f"-{color}?{style}")
            alt = f"{b['label']} {b['message']}"
        out.append((url, alt, b.get("link", "")))
    return out


def snippets(cfg: dict) -> dict:
    a = cfg.get("asset_dir", "assets/readme").rstrip("/")
    theme = cfg.get("theme", "beige")
    s = {}
    hero = cfg.get("hero", {})
    s["hero"] = picture(a, "hero", f"{cfg['name']}：{hero.get('tagline', '')}".rstrip("："), "100%")
    s["lang"] = "\n".join(
        f'  <a href="{_attr(l["href"])}">{picture(a, "lang-" + l["id"], l["label"])}</a>' for l in cfg.get("languages", []))
    s["keys"] = "\n".join(
        f'  <a href="{_attr(k["href"])}">{picture(a, "key-" + k["id"], k["label"])}</a>' for k in cfg.get("keys", []))
    badges = []
    for url, alt, link in badge_urls(cfg, theme):
        img = f'<img src="{_attr(url)}" alt="{_attr(alt)}">'
        badges.append(f'  <a href="{_attr(link)}">{img}</a>' if link else f"  {img}")
    s["badges"] = "\n".join(badges)
    for sec in cfg.get("sections", []):
        s["section:" + sec["id"]] = picture(a, "sec-" + sec["id"], f"{sec['zh']} · {sec['en']}", "100%")
    return s


def render_template(template: str, cfg: dict) -> str:
    snip = snippets(cfg)

    def sub(m):
        key = m.group(1).strip()
        if key not in snip:
            raise KeyError(f"unknown placeholder {{{{kit:{key}}}}}; known: {sorted(snip)}")
        return snip[key]

    return re.sub(r"\{\{\s*kit:([^}]+)\}\}", sub, template)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def render_assets(cfg: dict, base_dir: Path) -> dict:
    """Return {filename: svg_text} for every asset in both modes."""
    theme = cfg.get("theme", "beige")
    animate = cfg.get("animate", True)
    files = {}
    for mode in MODES:
        p = palette(theme, mode)
        files[f"hero-{mode}.svg"] = hero_svg(cfg, p, base_dir, animate)
        for l in cfg.get("languages", []):
            files[f"lang-{l['id']}-{mode}.svg"] = keycap_svg(l["label"], "", p, accent=l.get("active", False))
        for k in cfg.get("keys", []):
            files[f"key-{k['id']}-{mode}.svg"] = keycap_svg(k["label"], k.get("tag", ""), p, accent=k.get("accent", False))
        for i, sec in enumerate(cfg.get("sections", []), 1):
            files[f"sec-{sec['id']}-{mode}.svg"] = section_svg(sec["en"], sec["zh"], i, p)
    return files


def preview_html(cfg: dict, files: dict) -> str:
    a = cfg.get("asset_dir", "assets/readme").rstrip("/")
    cols = []
    for mode, bg in (("day", "#ffffff"), ("night", "#0d1117")):
        imgs = [f for f in files if f.endswith(f"-{mode}.svg")]
        order = lambda f: (0 if f.startswith("lang") else 1 if f.startswith("hero") else 2 if f.startswith("key") else 3, f)
        wide = ' style="width:100%"'
        tags = "".join(
            f'<img src="{a}/{f}"{wide if f.startswith(("hero", "sec")) else ""}>'
            for f in sorted(imgs, key=order))
        cols.append(f'<section style="background:{bg};padding:24px;display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start">{tags}</section>')
    return ("<!doctype html><meta charset='utf-8'><title>readme-kit preview</title>"
            "<body style='margin:0;display:grid;grid-template-columns:1fr 1fr'>" + "".join(cols) + "</body>\n")


def build(config_path: Path, template: Path = None, readme: Path = None, preview: Path = None,
          gallery: Path = None) -> list:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    out_dir = base / cfg.get("asset_dir", "assets/readme")
    out_dir.mkdir(parents=True, exist_ok=True)
    files = render_assets(cfg, base)
    for name, svg in files.items():
        (out_dir / name).write_text(svg, encoding="utf-8")
    written = [out_dir / n for n in files]
    if template and readme:
        readme.write_text(render_template(template.read_text(encoding="utf-8"), cfg), encoding="utf-8")
        written.append(readme)
    if preview:
        preview.write_text(preview_html(cfg, files), encoding="utf-8")
        written.append(preview)
    if gallery:
        gallery.mkdir(parents=True, exist_ok=True)
        for theme in THEMES:
            for mode in MODES:
                path = gallery / f"hero-{theme}-{mode}.svg"
                path.write_text(hero_svg(dict(cfg, theme=theme), palette(theme, mode), base, cfg.get("animate", True)),
                                encoding="utf-8")
                written.append(path)
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", type=Path, help="readme-kit.json")
    ap.add_argument("--template", type=Path, help="README template with {{kit:...}} placeholders")
    ap.add_argument("--readme", type=Path, help="output README path (requires --template)")
    ap.add_argument("--preview", type=Path, help="write an HTML page showing day/night assets side by side")
    ap.add_argument("--gallery", type=Path, help="write the hero in every theme to this directory")
    args = ap.parse_args(argv)
    if bool(args.template) != bool(args.readme):
        ap.error("--template and --readme must be used together")
    written = build(args.config, args.template, args.readme, args.preview, args.gallery)
    print(f"wrote {len(written)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
