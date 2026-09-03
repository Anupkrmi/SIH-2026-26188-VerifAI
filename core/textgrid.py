"""Generic fixed-width character-grid rendering and reading.

core/glyphs.py + the matching code in core/mrz.py were built first, for the
MRZ band specifically. The VIZ fields need exactly the same technique --
render known characters in a known monospace font, cache them as
templates, segment a region into fixed-width cells, match each cell by
normalised cross-correlation -- so that logic lives here once and both
core/mrz.py and core/viz_ocr.py call it, instead of two near-duplicate
copies drifting apart.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def render_glyph(ch: str, font: ImageFont.FreeTypeFont, cell_w: int, cell_h: int) -> np.ndarray:
    img = Image.new("L", (cell_w, cell_h), color=255)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), ch, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (cell_w - w) // 2 - bbox[0]
    y = (cell_h - h) // 2 - bbox[1]
    if ch != " ":  # a blank cell should stay blank, not draw an invisible glyph off-center
        d.text((x, y), ch, font=font, fill=0)
    return np.asarray(img, dtype=np.uint8)


def build_templates(charset: str, font_path: str, font_size: int, cell_w: int, cell_h: int
                     ) -> dict[str, np.ndarray]:
    font = ImageFont.truetype(font_path, font_size)
    return {ch: render_glyph(ch, font, cell_w, cell_h) for ch in charset}


def save_templates(templates: dict[str, np.ndarray], path: Path) -> None:
    np.savez(path, **templates)


def load_templates(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    return {k: data[k] for k in data.files}


_MEMO: dict[str, dict[str, np.ndarray]] = {}


def get_templates(cache_path: Path, charset: str, font_path: str, font_size: int,
                   cell_w: int, cell_h: int) -> dict[str, np.ndarray]:
    """Memoised per process, cached to disk across runs, keyed by cache_path
    so MRZ (OCR-A) and VIZ (Consolas) templates never collide."""
    key = str(cache_path)
    if key in _MEMO:
        return _MEMO[key]
    if cache_path.exists():
        templates = load_templates(cache_path)
    else:
        templates = build_templates(charset, font_path, font_size, cell_w, cell_h)
        save_templates(templates, cache_path)
    _MEMO[key] = templates
    return templates


_MATCH_PAD = 4      # px of search slack; see match_glyph docstring
_BLANK_STD = 8.0     # below this, a cell is background, not a faint glyph


def match_glyph(cell: np.ndarray, templates: dict[str, np.ndarray],
                 charset: set[str] | None = None) -> tuple[str, float]:
    """Best-matching character for one cell via normalised cross-correlation.

    Padding the resized cell and taking the best-aligned score within a
    small search window (rather than a single zero-lag comparison) makes
    this tolerant of the few-pixel misalignment that's routine when the
    document is rendered at a different font size/cell size than the
    template cache -- a tight ring shape like '0' is far more sensitive to
    exact alignment than an open shape like 'U', so a zero-lag comparison
    made '0' lose near-ties it should have won by a wide margin. See
    docs/06 for the concrete case this was found and fixed against.

    A blank cell (no ink -- the common case in the VIZ charset, which
    includes ' ') is detected directly from pixel variance, BEFORE any
    correlation runs, and never compared against a ' ' template via
    matchTemplate. TM_CCOEFF_NORMED's normalisation divides by the
    template's own variance; a hand-authored blank template has exactly
    zero variance, so OpenCV returns a degenerate score (observed: a flat
    1.0) that beats every real letter regardless of the cell's actual
    content. Handling "blank" as a pixel-statistics question instead of a
    template-matching one sidesteps that division entirely, for any
    charset that happens to include a flat/constant template.
    """
    if cell.size == 0:
        return " ", -1.0
    th, tw = next(iter(templates.values())).shape
    resized = cv2.resize(cell, (tw, th), interpolation=cv2.INTER_AREA).astype(np.float32)
    if " " in templates and (charset is None or " " in charset) and resized.std() < _BLANK_STD:
        return " ", 1.0
    padded = cv2.copyMakeBorder(resized, _MATCH_PAD, _MATCH_PAD, _MATCH_PAD, _MATCH_PAD,
                                 cv2.BORDER_CONSTANT, value=255.0)
    candidates = ((ch, t) for ch, t in templates.items()
                  if ch != " " and (charset is None or ch in charset))
    best_char, best_score = " ", -2.0
    for ch, tmpl in candidates:
        result = cv2.matchTemplate(padded, tmpl.astype(np.float32), cv2.TM_CCOEFF_NORMED)
        score = float(result.max())
        if score > best_score:
            best_char, best_score = ch, score
    return best_char, best_score


def segment_row(row_img: np.ndarray, n_cols: int) -> list[np.ndarray]:
    """Split a single-row image into n_cols evenly-sized cells."""
    h, w = row_img.shape[:2]
    col_w = w // n_cols
    return [row_img[:, c * col_w:(c + 1) * col_w] for c in range(n_cols)]


def draw_char_grid(draw: ImageDraw.ImageDraw, text: str, x0: int, y0: int,
                    cell_w: int, cell_h: int, n_cols: int,
                    font: ImageFont.FreeTypeFont, fill) -> None:
    """Draw `text` left-aligned into n_cols fixed-width cells starting at
    (x0, y0), space-padded/truncated to exactly n_cols characters -- the
    rendering counterpart to segment_row + match_glyph reading it back."""
    text = text.upper()[:n_cols].ljust(n_cols)
    for col, ch in enumerate(text):
        if ch == " ":
            continue
        cell_x = x0 + col * cell_w
        bbox = draw.textbbox((0, 0), ch, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cx = cell_x + (cell_w - w) // 2 - bbox[0]
        cy = y0 + (cell_h - h) // 2 - bbox[1]
        draw.text((cx, cy), ch, font=font, fill=fill)


def read_char_grid(gray: np.ndarray, bbox_xywh: tuple[int, int, int, int], n_cols: int,
                    templates: dict[str, np.ndarray], charset: set[str] | None = None
                    ) -> tuple[str, list[float]]:
    """Read n_cols fixed-width characters from a region, returns
    (text.rstrip(), per-cell confidence). The reading counterpart to
    draw_char_grid."""
    x, y, w, h = bbox_xywh
    row = gray[y:y + h, x:x + w]
    cells = segment_row(row, n_cols)
    chars, confs = [], []
    for cell in cells:
        ch, score = match_glyph(cell, templates, charset=charset)
        chars.append(ch)
        confs.append(score)
    return "".join(chars).rstrip(), confs
