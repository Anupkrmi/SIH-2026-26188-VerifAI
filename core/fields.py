"""The one shared layout both the generator (synth/passport.py) and every
reader (crosszone, forensics, face) agree on. Coordinates are computed once
here so the two sides can never silently disagree about where a field is --
that class of bug (generator and reader each hardcoding their own guess at
a bounding box) is the whole reason this file exists instead of two.

VIZ field values are rendered as fixed-width, uppercase, monospace text
(Consolas) and read back with the same template-matching technique used
for the MRZ (see core/textgrid.py) -- not a general OCR engine. This also
happens to be realistic: real passport data pages print the visual zone in
uppercase, block-letter style.
"""
from __future__ import annotations

from config import DOC_SIZE

W, H = DOC_SIZE

PORTRAIT_BBOX = (60, 150, 280, 430)   # x0, y0, x1, y1

# MRZ band: two lines, 44 columns, sized to sit inside the bottom margin.
MRZ_CELL_W = 20
MRZ_CELL_H = 32
MRZ_COLS = 44
MRZ_MARGIN_X = 16
MRZ_BAND_X = MRZ_MARGIN_X
MRZ_BAND_Y = H - (2 * MRZ_CELL_H) - 24
MRZ_BAND_W = MRZ_COLS * MRZ_CELL_W
MRZ_BAND_H = 2 * MRZ_CELL_H
MRZ_BAND_BBOX = (MRZ_BAND_X, MRZ_BAND_Y, MRZ_BAND_W, MRZ_BAND_H)  # x, y, w, h

# VIZ fields: fixed-width monospace grid, one row per field.
VIZ_CELL_W = 15
VIZ_CELL_H = 26
VIZ_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "

_ROW_Y0 = 150
_ROW_H = 46
VIZ_VALUE_X = 520

# (key, label, n_cols)
VIZ_FIELD_ORDER = [
    ("surname", "SURNAME", 20),
    ("given_names", "GIVEN NAMES", 20),
    ("passport_number", "PASSPORT NO", 9),
    ("nationality", "NATIONALITY", 3),
    ("date_of_birth", "DATE OF BIRTH", 11),   # "24 JAN 1977"
    ("sex", "SEX", 1),
    ("date_of_issue", "DATE OF ISSUE", 11),
    ("date_of_expiry", "DATE OF EXPIRY", 11),
]
VIZ_LABEL_X = 320

VIZ_LAYOUT: dict[str, dict] = {}
for _i, (_key, _label, _n_cols) in enumerate(VIZ_FIELD_ORDER):
    _y = _ROW_Y0 + _i * _ROW_H
    _w = _n_cols * VIZ_CELL_W
    VIZ_LAYOUT[_key] = {
        "label": _label,
        "n_cols": _n_cols,
        "label_pos": (VIZ_LABEL_X, _y),
        "value_bbox_xywh": (VIZ_VALUE_X, _y, _w, VIZ_CELL_H),
        "value_bbox": (VIZ_VALUE_X, _y, VIZ_VALUE_X + _w, _y + VIZ_CELL_H),
    }


def crop(img, bbox_xyxy_or_xywh, is_xywh: bool = False):
    """Crop a numpy image (H, W[, C]) to a bbox. Accepts either
    (x0, y0, x1, y1) or, if is_xywh, (x, y, w, h)."""
    if is_xywh:
        x, y, w, h = bbox_xyxy_or_xywh
        x0, y0, x1, y1 = x, y, x + w, y + h
    else:
        x0, y0, x1, y1 = bbox_xyxy_or_xywh
    return img[y0:y1, x0:x1]
