"""Thin wrapper over RapidOCR (ONNX runtime backend -- no torch/paddle; see
PLAN_realdoc.md for why this backend was chosen and how it was verified not
to disturb the opencv-contrib-python install core/face already depends on).

Mode A's MRZ/VIZ readers (core/mrz.py, core/textgrid.py) stay on their own
exact template-matching path against our own rendered font -- this module
is only ever used for arbitrary real documents, where no such registry of
known fields/fonts exists.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_engine = None


@dataclass
class OcrWord:
    text: str
    confidence: float
    box: tuple                # 4 (x, y) corner points, as returned by RapidOCR


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def extract_text(bgr: np.ndarray) -> list[OcrWord]:
    """Every text region RapidOCR finds, confidence included. Never filters
    or corrects anything -- core/realdoc/fields.py decides what's usable."""
    engine = _get_engine()
    result, _elapse = engine(bgr)
    if not result:
        return []
    return [OcrWord(text=text, confidence=float(score), box=tuple(map(tuple, box)))
            for box, text, score in result]


def full_text(words: list[OcrWord]) -> str:
    return " ".join(w.text for w in words)
