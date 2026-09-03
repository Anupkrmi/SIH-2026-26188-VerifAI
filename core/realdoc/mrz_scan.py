"""Best-effort MRZ discovery on an arbitrary real document. Reuses
core/mrz.py's real ICAO checksum math and its bottom-of-page band-locator
fallback unchanged -- nothing here is a second implementation of either.

Four distinct outcomes, not a boolean, because "no MRZ" and "an MRZ we
couldn't read" and "an MRZ that's actually wrong" are three different
claims and collapsing them loses exactly the information a screening
officer needs:

  NOT_DETECTED         -- nothing MRZ-shaped found. Ordinary for a college
                           ID, marksheet, or driving licence. Not suspicious.
  INSUFFICIENT_QUALITY -- an MRZ-shaped, correctly-positioned band was
                           found, but the glyph read isn't trustworthy
                           (scan resolution/skew/compression) -- something
                           IS there, we just can't certify what it says.
  DETECTED_VALID       -- read with real confidence, every check digit
                           matches what it protects.
  DETECTED_INVALID     -- read with real confidence, at least one check
                           digit does not match -- a genuine finding, not a
                           guess.

Never fabricates a checksum failure out of ordinary body text: the
plausibility gate (charset, leading character) runs BEFORE the confidence
threshold, and both run before any checksum is even computed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from core.mrz import CHARSET, locate_band, read_td3, validate_checkdigits

_MIN_MEAN_CONFIDENCE = 0.45   # match_glyph's TM_CCOEFF_NORMED scale is [-1, 1];
                              # a heuristic gate, not calibrated against real
                              # adversarial documents -- see core/textgrid.py.
_VALID_LEAD_CHARS = set("PIAC")  # ICAO document-type leads: P=passport, I/A/C=ID-card family (TD1/TD2)
_MIN_BAND_WIDTH = 200
_MIN_BAND_HEIGHT = 20

_STATUSES = {"NOT_DETECTED", "INSUFFICIENT_QUALITY", "DETECTED_VALID", "DETECTED_INVALID"}


@dataclass
class MrzScanResult:
    status: str                                                        # one of _STATUSES
    line1: str = ""
    line2: str = ""
    checks: list = field(default_factory=list)                        # core.mrz.MrzCheck, only if a checksum was actually computed
    bbox: tuple[int, int, int, int] | None = None                     # (x, y, w, h), whenever something MRZ-shaped was located

    @property
    def detected(self) -> bool:
        """Coarse present/absent view for callers (classification, the
        ladder's other steps) that only need to know "was there anything
        MRZ-shaped here at all" -- True for all three non-NOT_DETECTED
        statuses, including a low-quality read we chose not to trust."""
        return self.status != "NOT_DETECTED"


def try_read_mrz(gray: np.ndarray) -> MrzScanResult:
    try:
        bbox = locate_band(gray, nominal_bbox=None)
    except ValueError:
        return MrzScanResult(status="NOT_DETECTED")

    _x, _y, w, h = bbox
    if w < _MIN_BAND_WIDTH or h < _MIN_BAND_HEIGHT:
        return MrzScanResult(status="NOT_DETECTED")

    try:
        line1, line2, confidences = read_td3(gray, nominal_bbox=bbox)
    except Exception:
        return MrzScanResult(status="NOT_DETECTED")

    plausible_charset = bool(line1) and bool(line2) and all(c in CHARSET for c in line1 + line2)
    plausible_lead = line1[:1] in _VALID_LEAD_CHARS
    if not (plausible_charset and plausible_lead):
        # Doesn't even look like MRZ syntax -- almost certainly ordinary
        # body text the bottom-third locator picked up, not a real MRZ.
        return MrzScanResult(status="NOT_DETECTED")

    flat_conf = [c for row in confidences for c in row]
    mean_conf = sum(flat_conf) / len(flat_conf) if flat_conf else -1.0
    if mean_conf < _MIN_MEAN_CONFIDENCE:
        return MrzScanResult(status="INSUFFICIENT_QUALITY", bbox=bbox)

    checks = validate_checkdigits(line2)
    status = "DETECTED_VALID" if all(c.ok for c in checks) else "DETECTED_INVALID"
    return MrzScanResult(status=status, line1=line1, line2=line2, checks=checks, bbox=bbox)


def try_read_mrz_robust(bgr: np.ndarray) -> MrzScanResult:
    """try_read_mrz() on the original image; if that comes back
    NOT_DETECTED, retry on a document-boundary-cropped-and-deskewed
    version (core/realdoc/page_crop.py) in case the upload is a full
    scanned/photographed PAGE with margin around the actual document --
    common for a passport PDF, never true of our own synthetic corpus.

    Tested against a real passport PDF specifically: page_crop found no
    confident boundary to crop to (the page already IS approximately the
    document, no separate margin to remove), so this fell through to the
    same NOT_DETECTED both times for that case -- documented honestly in
    README.md rather than claimed as a fix it isn't. Kept because it's a
    real, safe capability for the (different, also real) case of a
    passport scanned onto a larger sheet with visible margin, which this
    one test document didn't happen to be."""
    original = try_read_mrz(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr)
    if original.status in ("DETECTED_VALID", "DETECTED_INVALID"):
        return original

    from core.realdoc.page_crop import try_crop_to_document
    cropped_bgr = try_crop_to_document(bgr)
    if cropped_bgr is bgr:
        return original  # page_crop found nothing to crop to -- no second attempt to make

    cropped_gray = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2GRAY)
    retried = try_read_mrz(cropped_gray)
    # Prefer whichever attempt found something more informative than
    # NOT_DETECTED; if both did, prefer the original (no crop-introduced
    # distortion) unless the crop specifically upgraded to a confident read.
    if original.status == "NOT_DETECTED" and retried.status != "NOT_DETECTED":
        return retried
    return original
