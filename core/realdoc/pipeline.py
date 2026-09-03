"""Orchestrates a REAL, arbitrary document (+ optional person photo)
through a capability-aware Trust Ladder. Mode A's core/pipeline.py (the
fixed-template UTO passport + Attack Wall) is untouched and unrelated --
this is Mode B, wired from ui/pages.py's "Real Document" branch only.
"""
from __future__ import annotations

import cv2
import numpy as np

from core.face.pipeline import verify as face_verify
from core.forensics import ela, noise, photo_region, recapture
from core.realdoc import classify, mrz_scan, portrait
from core.realdoc.fields import ExtractedField, extract_fields
from core.realdoc.ocr import OcrWord, extract_text, full_text
from core.realdoc.risk import LadderStep, RealDocVerdict, fuse_realdoc
from core.realdoc.validate import validate_fields
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier

_FORENSIC_CHECKS = {"photo_region_anomaly", "noise_residual_anomaly", "recapture_anomaly"}
_RULE_CHECKS = {"realdoc_dob_future", "realdoc_dob_age", "realdoc_expired"}
_CONSISTENCY_CHECKS = {"realdoc_issue_after_expiry"}

_MRZ_LADDER = {
    "NOT_DETECTED": ("NOT_APPLICABLE", "MRZ not present / not detected"),
    "INSUFFICIENT_QUALITY": ("REVIEW", "MRZ-shaped region found but not reliably readable (scan quality)"),
    "DETECTED_VALID": ("VERIFIED", "MRZ detected, all check digits valid"),
    "DETECTED_INVALID": ("FAILED", "MRZ detected, one or more check digits invalid"),
}


def _advisory_only(signal: Signal) -> Signal:
    """Downgrade a forensic FAIL to an advisory, zero-weight WEAK signal.

    core/forensics/photo_region.py's threshold was measured against
    exactly one geometry: the synthetic UTO template's fixed 280x430
    portrait box with one real photo pasted in (see its own module
    docstring's recalibration history -- this is its SECOND calibration
    incident, not its first). Validating Mode B against real documents
    surfaced a systematic false positive: photo_region_anomaly FAILed on
    every one of 6 genuine real documents tested (college ID, passport, 2
    marksheets, a university marksheet, Aadhaar) -- college-ID and
    passport portraits are a different size/compression/lighting profile
    than the one calibration point, and no real forged document was
    available to establish a real-document threshold either way. Absent
    that calibration, treating a FAIL here as a confident finding would be
    exactly the false certainty this project's language rule forbids;
    advisory-only (REVIEW on the ladder, zero contribution to score) is
    the honest claim until it's actually measured against real forgeries.
    noise_residual_anomaly and recapture_anomaly get the same treatment
    for the same reason: neither was calibrated on anything but the same
    synthetic corpus. error_level_analysis is untouched -- Mode A already
    treats it as permanently WEAK/advisory by construction."""
    if signal.severity != Severity.FAIL:
        return signal
    return Signal(tier=signal.tier, check=signal.check, severity=Severity.WEAK, weight=0,
                   message=f"ADVISORY: {signal.message} (not independently calibrated for arbitrary real documents)",
                   detail=signal.detail)


def _step_status(signals: list[Signal], check_names: set[str], if_none: str) -> str:
    relevant = [s for s in signals if s.check in check_names]
    if not relevant:
        return if_none
    if any(s.severity == Severity.FAIL for s in relevant):
        return "FAILED"
    if any(s.severity == Severity.WEAK for s in relevant):
        # WEAK means the check ran but couldn't reach a real conclusion
        # (e.g. face_verification with no face found, or a quality-gate
        # rejection) -- that is a REVIEW, not a clean VERIFIED pass.
        return "REVIEW"
    return "VERIFIED"


def _build_ladder(ocr_ran: bool, fields_present: bool, mrz: mrz_scan.MrzScanResult,
                    portrait_found: bool, person_provided: bool, signals: list[Signal]) -> list[LadderStep]:
    steps = [
        LadderStep("Document Detection", "VERIFIED" if ocr_ran else "REVIEW",
                    "Text regions found" if ocr_ran else "No readable text detected"),
        LadderStep("OCR / Field Extraction", "VERIFIED" if fields_present else "REVIEW",
                    "" if fields_present else "OCR ran but no recognizable fields matched"),
        LadderStep("MRZ Detection", *_MRZ_LADDER[mrz.status]),
        LadderStep("Rule Validation", _step_status(signals, _RULE_CHECKS, "NOT_APPLICABLE")),
        LadderStep("Cross-Field Consistency", _step_status(signals, _CONSISTENCY_CHECKS, "NOT_APPLICABLE")),
        LadderStep("Forensic Analysis", _step_status(signals, _FORENSIC_CHECKS, "REVIEW")),
        LadderStep("Biometric Verification",
                    _step_status(signals, {"face_verification"}, "REVIEW") if (portrait_found and person_provided)
                    else "NOT_APPLICABLE",
                    "" if portrait_found else "No reliable document portrait detected" if not person_provided
                    else "No person photo provided"),
        LadderStep("Cryptographic Integrity", "NOT_APPLICABLE", "No registered demo signature for uploaded documents"),
    ]
    return steps


def screen_real_document(doc_bgr: np.ndarray, person_bgr: np.ndarray | None = None,
                           manual_portrait_bbox: tuple[int, int, int, int] | None = None
                           ) -> tuple[RealDocVerdict, dict]:
    """Returns (verdict, context). context carries everything the UI needs
    to render the capability panel, OCR field table, and portrait/person
    comparison images without recomputing anything.

    manual_portrait_bbox (x0, y0, x1, y1): an officer-specified override for
    when automatic portrait detection is absent or visibly wrong -- a
    location fix, not a quality one. It changes which region forensics and
    face comparison look at; it cannot make genuinely blurry source pixels
    sharp (the college ID's REVIEW result was traced to the card's own
    printed photo failing the blur floor, not to a wrong region -- a manual
    box over the exact same pixels would fail the same quality gate)."""
    policy = load_policy()
    gray = cv2.cvtColor(doc_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    words: list[OcrWord] = extract_text(doc_bgr)
    text = full_text(words).upper()
    ocr_ran = len(words) > 0

    mrz_result = mrz_scan.try_read_mrz_robust(doc_bgr)
    # A confidently-read MRZ (valid or invalid checksums) is real evidence
    # of a passport-style layout; an INSUFFICIENT_QUALITY read is not --
    # it only means *something* MRZ-shaped and low-confidence was found in
    # the bottom-of-page scan, which dense body text on a certificate or
    # marksheet can trigger too (see core/realdoc/mrz_scan.py's docstring).
    mrz_is_strong_evidence = mrz_result.status in ("DETECTED_VALID", "DETECTED_INVALID")
    doc_type, doc_type_note = classify.classify_document(text, mrz_is_strong_evidence, w / h)

    fields: dict[str, ExtractedField] = extract_fields(words) if ocr_ran else {}
    signals: list[Signal] = list(validate_fields(fields, policy)) if ocr_ran else []

    if mrz_result.detected:
        weight = int(policy["risk_weights"]["mrz_checksum_fail"])
        for c in mrz_result.checks:
            signals.append(Signal(
                tier=Tier.RULES, check=f"realdoc_mrz_{c.field}",
                severity=Severity.PASS if c.ok else Severity.FAIL,
                weight=0 if c.ok else weight,
                message=(f"MRZ check digit for {c.field} is valid" if c.ok else
                          f"MRZ check digit for {c.field} does not match (expected {c.expected}, found {c.found})")))

    if manual_portrait_bbox is not None:
        x0, y0, x1, y1 = manual_portrait_bbox
        portrait_bbox = manual_portrait_bbox if (x1 > x0 and y1 > y0) else None
    else:
        portrait_row = portrait.find_portrait(doc_bgr)
        portrait_bbox = portrait.bbox_xyxy(portrait_row, doc_bgr.shape) if portrait_row is not None else None
    if portrait_bbox is not None:
        signals.append(_advisory_only(photo_region.check(gray, portrait_bbox, policy=policy)))

    exclude = mrz_result.bbox if mrz_result.detected else None
    signals.append(_advisory_only(noise.check(gray, exclude_bbox_xywh=exclude, policy=policy)))
    signals.append(_advisory_only(recapture.check(gray, policy=policy)))
    signals.append(ela.check(gray))

    if portrait_bbox is not None and person_bgr is not None:
        # verify() re-detects the face within the FULL document image itself
        # (its own contract, unchanged) -- portrait_bbox already gates
        # *whether* this call happens at all (conservative: skip rather
        # than guess when no plausible portrait region exists). For an
        # AUTO-detected box the full document is passed through unchanged,
        # exactly as before: verify()'s own detection independently
        # confirms the same region. For a MANUAL box the whole point is to
        # look somewhere auto-detection didn't (or got wrong) -- passing
        # the full image would let verify() re-detect wherever IT wants
        # and silently ignore the officer's selection, so the crop itself
        # is passed instead.
        face_input = doc_bgr
        if manual_portrait_bbox is not None:
            x0, y0, x1, y1 = manual_portrait_bbox
            face_input = doc_bgr[y0:y1, x0:x1]
        signals.append(face_verify(face_input, person_bgr))

    steps = _build_ladder(ocr_ran, any(f.status != "NOT_DETECTED" for f in fields.values()), mrz_result,
                           portrait_bbox is not None, person_bgr is not None, signals)
    insufficient_evidence = not ocr_ran and portrait_bbox is None

    verdict = fuse_realdoc(signals, steps, insufficient_evidence, policy)
    context = {
        "gray": gray, "words": words, "text": text, "fields": fields,
        "doc_type": doc_type, "doc_type_note": doc_type_note,
        "mrz": mrz_result, "portrait_bbox": portrait_bbox,
        "portrait_manual": manual_portrait_bbox is not None and portrait_bbox is not None,
        "capabilities": {
            "OCR": ocr_ran,
            "MRZ": mrz_result.detected,
            "PORTRAIT": portrait_bbox is not None,
            "FACE COMPARISON": portrait_bbox is not None and person_bgr is not None,
            "RULE VALIDATION": ocr_ran,
            "FORENSICS": True,
            "CRYPTOGRAPHIC CHECK": False,
        },
    }
    return verdict, context
