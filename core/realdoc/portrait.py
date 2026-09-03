"""Portrait/face-region discovery on arbitrary real documents.

The synthetic Mode A pipeline knows the exact portrait bbox
(core/fields.py::PORTRAIT_BBOX) because it drew the document itself. A real
document has no such registry -- this module finds the most plausible
portrait candidate by scoring every YuNet detection on the full page, or
returns None rather than guessing. core/realdoc/pipeline.py treats None as
"PORTRAIT NOT RELIABLY DETECTED" and skips biometric comparison entirely.
"""
from __future__ import annotations

import numpy as np

from core.face.pipeline import MIN_FACE_SIZE, detect_faces

MIN_CONFIDENCE = 0.75      # above YuNet's own 0.7 floor -- a document scan
                           # has more clutter than a clean live capture

# A fractional size floor (percent of the page's shorter side) does not
# transfer across documents rendered at very different scales: a marksheet
# false positive (YuNet found a small seal/stamp graphic at confidence
# 0.93) measured ~4% of its page width, but a genuine, correctly-detected
# face on a real Aadhaar PDF rendered as a large full page measured only
# ~3.8% -- almost the same fraction. An ABSOLUTE floor is scale-invariant
# instead: MIN_FACE_SIZE is the same floor the live quality gate already
# requires (core.face.pipeline.quality_gate), so nothing smaller could
# ever pass biometric comparison anyway. Real face-shaped ASPECT RATIO is
# the actual discriminator that separates the two cases -- the marksheet's
# false positive measured width/height 0.93 (near-square, seal-shaped);
# every real ID portrait measured (passport 0.71, college ID 0.87, two
# different Aadhaar photos 0.79 and 0.73) sits in a materially narrower,
# taller-than-wide band.
MIN_ASPECT_RATIO = 0.55    # width/height -- rejects unusually wide boxes
MAX_ASPECT_RATIO = 0.90    # rejects near-square/circular boxes (seals, logos, stamps)


def find_portrait(bgr: np.ndarray) -> np.ndarray | None:
    """Best-scoring YuNet face row (bbox+landmarks+score, same 15-value
    shape as core.face.pipeline.detect_largest_face), or None if nothing on
    the page plausibly reads as a document portrait."""
    h, w = bgr.shape[:2]
    faces = detect_faces(bgr)
    if len(faces) == 0:
        return None

    best_row, best_score = None, -1.0
    for row in faces:
        x, y, fw, fh, conf = row[0], row[1], row[2], row[3], row[-1]
        aspect = fw / fh if fh > 0 else 0
        if (conf < MIN_CONFIDENCE or min(fw, fh) < MIN_FACE_SIZE
                or not (MIN_ASPECT_RATIO <= aspect <= MAX_ASPECT_RATIO)):
            continue
        # ID portraits sit in a corner/side column, not dead centre (which
        # on an ID card or marksheet is more often a seal, logo, or block of
        # body text) -- prefer larger, more confident, and off-centre faces.
        cx = x + fw / 2
        center_bias = abs(cx - w / 2) / (w / 2)
        area_frac = (fw * fh) / (w * h)
        score = conf + 0.5 * area_frac + 0.2 * center_bias
        if score > best_score:
            best_score, best_row = score, row
    return best_row


def bbox_xyxy(face_row: np.ndarray, image_shape: tuple[int, int]) -> tuple[int, int, int, int]:
    """face_row's bbox, clamped to the image bounds, as (x0, y0, x1, y1)."""
    h, w = image_shape[:2]
    x, y, fw, fh = face_row[:4].astype(int)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(w, x + fw), min(h, y + fh)
    return x0, y0, x1, y1
