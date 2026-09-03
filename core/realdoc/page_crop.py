"""Passport-specific preprocessing: find and deskew the actual document
page within a larger scanned/photographed image before handing it to the
existing MRZ locator.

Real passport uploads are often a full PDF/photo page with margin, a
table surface, or a hand around the passport itself -- unlike the
synthetic corpus, which IS the data page with no surrounding content.
core/mrz.py::locate_band's bottom-fraction heuristic assumes the latter;
validating it against a real passport PDF showed it grabbing a band
spanning 37% of the page height because scattered page content (not an
isolated 2-line MRZ) cleared its density floor. This module gives that
locator a tighter, straightened crop to search instead of touching its
logic.

Best-effort and conservative by construction: if no confident document
boundary is found, or the found boundary produces something degenerate,
the original image is returned unchanged -- never a forced, wrong crop.
"""
from __future__ import annotations

import cv2
import numpy as np

_MIN_CONTOUR_AREA_FRACTION = 0.15  # the document must be a substantial part of the page to trust cropping to it


def _find_document_corners(bgr: np.ndarray) -> np.ndarray | None:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    page_area = bgr.shape[0] * bgr.shape[1]
    if cv2.contourArea(largest) < _MIN_CONTOUR_AREA_FRACTION * page_area:
        return None  # nothing large/confident enough to be "the document" as opposed to page noise

    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)
    if len(approx) == 4:
        return approx.reshape(4, 2).astype(np.float32)
    x, y, w, h = cv2.boundingRect(largest)
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32)


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Returns corners ordered [top-left, top-right, bottom-right, bottom-left]."""
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).flatten()
    tl, br = pts[np.argmin(s)], pts[np.argmax(s)]
    tr, bl = pts[np.argmin(diff)], pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)


def _warp_to_rectangle(bgr: np.ndarray, corners: np.ndarray) -> np.ndarray:
    tl, tr, br, bl = _order_corners(corners)
    max_w = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    max_h = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl], dtype=np.float32), dst)
    return cv2.warpPerspective(bgr, matrix, (max_w, max_h))


def try_crop_to_document(bgr: np.ndarray) -> np.ndarray:
    """Best-effort tighter, deskewed crop of the document within a larger
    page image. Returns bgr UNCHANGED whenever no confident boundary is
    found or the result would be degenerate -- never raises, never forces
    a wrong crop onto a caller."""
    corners = _find_document_corners(bgr)
    if corners is None:
        return bgr
    try:
        cropped = _warp_to_rectangle(bgr, corners)
    except Exception:
        return bgr
    h, w = cropped.shape[:2]
    if h < 50 or w < 50:
        return bgr
    return cropped
