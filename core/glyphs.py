"""MRZ glyph templates: the 37 characters (A-Z, 0-9, <) rendered once in
the real OCR-A Extended font. Thin, MRZ-specific configuration over the
shared machinery in core/textgrid.py (which also serves the VIZ reader in
core/viz_ocr.py) -- kept as its own module because callers already import
`from core.glyphs import get_templates` and there is no reason to disturb
that for a refactor that changes nothing about MRZ behaviour.
"""
from __future__ import annotations

from config import FONTS, MODEL_FILES
from core.mrz import CHARSET
from core.textgrid import get_templates as _get_templates

CELL_W, CELL_H = 26, 40
FONT_SIZE = 34


def get_templates():
    return _get_templates(MODEL_FILES["glyphs"], CHARSET, FONTS["mrz"], FONT_SIZE, CELL_W, CELL_H)


if __name__ == "__main__":
    t = get_templates()
    print(f"{len(t)} glyph templates ready, cell {CELL_W}x{CELL_H}, cached at {MODEL_FILES['glyphs']}")
