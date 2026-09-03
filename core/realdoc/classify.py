"""Lightweight, best-effort document-type guess -- not a research-grade
classifier (the user-facing label always says so). Combines MRZ presence,
OCR keyword hits, and aspect ratio, in that order of reliability.
core/realdoc/pipeline.py uses the result only to label the case; it never
gates which checks run.
"""
from __future__ import annotations

_KEYWORDS: dict[str, list[str]] = {
    "PASSPORT": ["PASSPORT", "PASSEPORT", "TRAVEL DOCUMENT"],
    "IDENTITY CARD": ["IDENTITY CARD", "AADHAAR", "UNIQUE IDENTIFICATION",
                       "GOVERNMENT OF INDIA", "NATIONAL ID"],
    "DRIVING LICENCE": ["DRIVING LICENCE", "DRIVING LICENSE", "TRANSPORT DEPARTMENT", "LMV", "MCWG"],
    "COLLEGE ID": ["COLLEGE", "UNIVERSITY", "STUDENT ID", "INSTITUTE OF TECHNOLOGY", "CAMPUS"],
    "EDUCATIONAL DOCUMENT": ["MARKSHEET", "MARK SHEET", "GRADE", "EXAMINATION",
                              "BOARD OF", "TRANSCRIPT", "CGPA", "ROLL NO"],
}


def classify_document(full_text_upper: str, mrz_detected: bool, aspect_ratio: float) -> tuple[str, str]:
    """Returns (label, note). label is one of the categories above or
    "UNKNOWN"; note states the basis, so the UI never presents the guess as
    more certain than it is."""
    if mrz_detected:
        return "PASSPORT", "MRZ detected — passport-style layout"

    hits = {label: sum(1 for kw in kws if kw in full_text_upper) for label, kws in _KEYWORDS.items()}
    label, count = max(hits.items(), key=lambda kv: kv[1])
    if count > 0:
        return label, f"keyword match ({count} hit(s) in extracted text)"

    if 1.30 <= aspect_ratio <= 1.75:
        return "IDENTITY CARD", "best-effort: card-like aspect ratio, no keyword match"

    return "UNKNOWN", "no MRZ, no keyword match — best-effort screening only"
