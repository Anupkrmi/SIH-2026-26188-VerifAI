"""Real Document Screening mode (Mode B) tests. Mode A's own test files are
proof-by-non-modification here: nothing in core/realdoc/ is imported by
core/pipeline.py, core/risk.py, or core/types.py, so the existing suite
passing unchanged (see test_pipeline.py, test_risk.py, test_crypto.py, the
Attack Wall coverage in ui/actions.py's own call sites) already demonstrates
Mode A is untouched. This file covers only the new Mode B code paths.

A second, consenting identity is on file at
data/portraits/second_person.jpg.jpeg (added specifically for a genuine
end-to-end mismatch test -- the Attack Wall's disabled FACE MISMATCH
button still only has the original single identity, and stays disabled;
that button is Mode A's concern, unaffected by this file). Both a genuine
mismatch test and a forced-threshold logic test are kept side by side --
see test_face_mismatch_branch_produces_fail_with_a_real_second_identity
and test_face_mismatch_branch_logic_with_forced_threshold below.
"""
from __future__ import annotations

import glob
from pathlib import Path

import cv2
import numpy as np
import pytest

from core.face.pipeline import verify as face_verify
from core.realdoc import mrz_scan
from core.realdoc.fields import ExtractedField, extract_fields
from core.realdoc.ocr import OcrWord
from core.realdoc.page_crop import try_crop_to_document
from core.realdoc.pipeline import screen_real_document
from core.realdoc.risk import LadderStep, fuse_realdoc
from core.realdoc.validate import validate_fields
from core.types import Severity, Signal, Tier

GENUINE = "data/documents/demo_0001.png"
_PORTRAITS = sorted(glob.glob("data/portraits/*.jpg")) + sorted(glob.glob("data/portraits/*.png"))
_HAS_REAL_PORTRAIT = len(_PORTRAITS) >= 1
_SECOND_PERSON = "data/portraits/second_person.jpg.jpeg"
_HAS_SECOND_PERSON = Path(_SECOND_PERSON).exists()


def _load(path: str) -> np.ndarray:
    img = cv2.imread(path)
    assert img is not None, f"fixture missing: {path}"
    return img


# ---------------------------------------------------------------- upload ---

def test_arbitrary_dimensions_are_accepted_without_resizing():
    """Mode A hard-requires exactly 1000x700; Mode B must not -- an odd,
    non-template size must run end-to-end with no crash and no forced
    resize anywhere in the pipeline."""
    odd = np.full((333, 777, 3), 220, dtype=np.uint8)
    verdict, ctx = screen_real_document(odd)
    assert ctx["gray"].shape == (333, 777)
    assert verdict.band in ("LOW", "MEDIUM", "HIGH", "REVIEW")


# ------------------------------------------------------------- portrait ---

def test_document_without_a_detectable_portrait_skips_face_matching():
    blank = np.full((900, 700, 3), 255, dtype=np.uint8)  # no face anywhere on the page
    person = _load(_PORTRAITS[0]) if _HAS_REAL_PORTRAIT else blank
    verdict, ctx = screen_real_document(blank, person_bgr=person)
    assert ctx["capabilities"]["PORTRAIT"] is False
    assert ctx["capabilities"]["FACE COMPARISON"] is False
    bio_step = next(s for s in verdict.steps if s.name == "Biometric Verification")
    assert bio_step.status == "NOT_APPLICABLE"
    assert not any(s.check == "face_verification" for s in verdict.signals)


@pytest.mark.skipif(not _HAS_REAL_PORTRAIT, reason="no real photo on file in data/portraits/")
def test_matching_person_photo_against_the_document_portrait_is_a_match():
    doc = _load(GENUINE)
    person = _load(_PORTRAITS[0])
    verdict, ctx = screen_real_document(doc, person_bgr=person)
    assert ctx["capabilities"]["FACE COMPARISON"] is True
    face_signal = next(s for s in verdict.signals if s.check == "face_verification")
    assert face_signal.severity == Severity.PASS
    bio_step = next(s for s in verdict.steps if s.name == "Biometric Verification")
    assert bio_step.status == "VERIFIED"


@pytest.mark.skipif(not _HAS_SECOND_PERSON, reason="no second consenting identity on file at data/portraits/second_person.jpg.jpeg")
def test_face_mismatch_branch_produces_fail_with_a_real_second_identity():
    """Genuine end-to-end mismatch: a real second consenting person's
    photo against the document portrait, no forced threshold. Measured,
    not asserted against a specific number (the exact similarity is
    reported in the validation notes, not pinned here) -- only that it's
    a real FAIL below the real, unmodified threshold."""
    doc = _load(GENUINE)
    person = _load(_SECOND_PERSON)
    signal = face_verify(doc, person)
    assert signal.severity == Severity.FAIL
    assert signal.weight > 0
    assert signal.detail["similarity"] < signal.detail["threshold"]


@pytest.mark.skipif(not _HAS_REAL_PORTRAIT, reason="no real photo on file in data/portraits/")
def test_face_mismatch_branch_logic_with_forced_threshold():
    """Belt-and-suspenders: proves the FAIL branch's logic/format is
    correct (severity, weight, message) independent of whether a second
    identity happens to be on file, by forcing it with a threshold cosine
    similarity can never reach. Kept alongside the genuine test above,
    not instead of it, now that a real second identity IS available."""
    doc = _load(GENUINE)
    person = _load(_PORTRAITS[0])
    signal = face_verify(doc, person, threshold=1.1)
    assert signal.severity == Severity.FAIL
    assert signal.weight > 0
    assert signal.detail["similarity"] < 1.1


@pytest.mark.skipif(not _HAS_SECOND_PERSON, reason="no second consenting identity on file at data/portraits/second_person.jpg.jpeg")
def test_end_to_end_mismatch_elevates_risk_through_the_full_pipeline():
    """Not just face_verify() in isolation -- the full screen_real_document
    pipeline, with a genuine second identity, should carry the mismatch
    through to a FAILED biometric ladder step and a non-zero score
    contribution, matching the CASE 2 demo scenario (document + a
    different consenting person -> elevated risk)."""
    doc = _load(GENUINE)
    person = _load(_SECOND_PERSON)
    verdict, ctx = screen_real_document(doc, person_bgr=person)
    face_signal = next(s for s in verdict.signals if s.check == "face_verification")
    assert face_signal.severity == Severity.FAIL
    bio_step = next(s for s in verdict.steps if s.name == "Biometric Verification")
    assert bio_step.status == "FAILED"
    assert verdict.score >= face_signal.weight


def test_poor_quality_face_photo_returns_review_not_a_score():
    """A quality-gate rejection (flat/zero-variance capture) must produce
    WEAK with no similarity number -- covered directly at the
    core.face.pipeline level in tests/test_face.py; this asserts the
    real-doc ladder renders that WEAK signal as REVIEW, not as a clean
    VERIFIED pass (the bug this test was written to catch: REVIEW status
    was being collapsed into VERIFIED before core/realdoc/pipeline.py's
    _step_status learned about Severity.WEAK)."""
    doc = _load(GENUINE)
    flat = np.full((300, 300, 3), 128, dtype=np.uint8)
    verdict, ctx = screen_real_document(doc, person_bgr=flat)
    if ctx["capabilities"]["PORTRAIT"]:
        bio_step = next(s for s in verdict.steps if s.name == "Biometric Verification")
        assert bio_step.status == "REVIEW"
        face_signal = next(s for s in verdict.signals if s.check == "face_verification")
        assert face_signal.severity == Severity.WEAK
        assert "similarity" not in face_signal.detail


# -------------------------------------------------------------- MRZ N/A ---

def test_no_mrz_present_never_reports_a_fabricated_checksum_failure():
    """Random noise must never produce a DETECTED_VALID/DETECTED_INVALID
    verdict (that would mean a checksum claim was made about content that
    isn't an MRZ at all). It CAN legitimately land on INSUFFICIENT_QUALITY
    if the plausibility gate (charset + lead character) happens to pass by
    chance -- that still makes zero checksum claims (checks stays empty);
    only a confident, checksum-backed status would be a fabrication."""
    noise = np.random.RandomState(0).randint(0, 255, (600, 400, 3), dtype=np.uint8)
    gray = cv2.cvtColor(noise, cv2.COLOR_BGR2GRAY)
    result = mrz_scan.try_read_mrz(gray)
    assert result.status not in ("DETECTED_VALID", "DETECTED_INVALID")
    assert result.checks == []


def test_realdoc_ladder_marks_mrz_not_applicable_when_absent():
    doc = np.full((900, 700, 3), 255, dtype=np.uint8)
    verdict, ctx = screen_real_document(doc)
    assert ctx["mrz"].detected is False
    mrz_step = next(s for s in verdict.steps if s.name == "MRZ Detection")
    assert mrz_step.status == "NOT_APPLICABLE"
    assert not any(s.check.startswith("realdoc_mrz_") for s in verdict.signals)


# ----------------------------------------------------------- crypto N/A ---

def test_crypto_is_always_not_applicable_in_real_document_mode():
    doc = _load(GENUINE)
    verdict, _ctx = screen_real_document(doc)
    crypto_step = next(s for s in verdict.steps if s.name == "Cryptographic Integrity")
    assert crypto_step.status == "NOT_APPLICABLE"
    assert not any(s.tier == Tier.CRYPTO for s in verdict.signals)


# ------------------------------------------------------------ validation ---

def test_future_dob_is_flagged():
    fields = {"date_of_birth": ExtractedField("2099-01-01", "EXTRACTED", "HIGH")}
    signals = validate_fields(fields)
    assert any(s.check == "realdoc_dob_future" and s.severity == Severity.FAIL for s in signals)


def test_consistent_issue_and_expiry_dates_pass():
    fields = {
        "date_of_issue": ExtractedField("2020-01-01", "EXTRACTED", "HIGH"),
        "date_of_expiry": ExtractedField("2030-01-01", "EXTRACTED", "HIGH"),
    }
    signals = validate_fields(fields)
    assert any(s.check == "realdoc_issue_after_expiry" and s.severity == Severity.PASS for s in signals)


def test_field_extraction_never_borrows_another_labels_line_as_a_value():
    """Regression: a label with no value of its own (its value line lost to
    OCR noise) must report NOT_DETECTED, never silently adopt the next
    field's label text as if it were its own value."""
    words = [OcrWord("NATIONALITY", 0.9, ()), OcrWord("DATE OF BIRTH", 0.9, ())]
    fields = extract_fields(words)
    assert fields["nationality"].status == "NOT_DETECTED"


def test_field_extraction_rejects_a_numeric_only_name_grab():
    words = [OcrWord("SURNAME", 0.9, ()), OcrWord("2024", 0.9, ())]
    fields = extract_fields(words)
    assert fields["name"].status == "NOT_DETECTED"


# --------------------------------------- Indian-ID label-independent values ---
# Found against a real Aadhaar PDF: none of these three values sit next to
# a label matching this project's original passport/college-ID-oriented
# keyword list at all, so all three were previously silently NOT_DETECTED
# despite being genuinely present and legible in the OCR text.

def test_spaced_aadhaar_style_number_is_extracted_without_a_label():
    words = [OcrWord("YOUR AADHAAR NUMBER", 0.8, ()), OcrWord("2878 8883 7088", 0.9, ())]
    fields = extract_fields(words)
    assert fields["document_number"].value == "287888837088"


def test_bare_gender_word_is_extracted_without_a_sex_or_gender_label():
    words = [OcrWord("Address:", 0.9, ()), OcrWord("/ MALE", 0.8, ())]
    fields = extract_fields(words)
    assert fields["gender"].value == "MALE"


def test_bare_m_or_f_alone_is_not_treated_as_gender():
    """Only the unambiguous full words are trusted label-independent --
    see core/realdoc/fields.py's own comment on why bare M/F is excluded
    (too easily a stray section letter or initial with nothing anchoring
    it to an actual gender field)."""
    words = [OcrWord("SECTION M", 0.9, ())]
    fields = extract_fields(words)
    assert fields["gender"].status == "NOT_DETECTED"


def test_name_is_inferred_positionally_from_the_line_before_a_found_dob():
    words = [OcrWord("Rajveer Singh Pall", 0.9, ()), OcrWord("D0B:17/12/2004", 0.8, ())]
    fields = extract_fields(words)
    assert fields["name"].value == "RAJVEER SINGH PALL"
    assert fields["name"].status == "UNCERTAIN"   # positional inference, not a labelled read


def test_name_positional_fallback_does_not_fire_without_a_found_dob():
    words = [OcrWord("Rajveer Singh Pall", 0.9, ()), OcrWord("Some other line", 0.8, ())]
    fields = extract_fields(words)
    assert fields["name"].status == "NOT_DETECTED"


def test_stacked_labels_pair_with_the_correctly_positioned_value():
    """Found live on a real passport: 'Date of Issue' and 'Date of
    Expiry' printed as two consecutive bare labels (no value on either
    label's own line), with BOTH values printed afterward as their own
    two-line block, in the same order. A naive "grab the very next line"
    rule paired Date of Issue's own value (03/04/2024) with the Date of
    Expiry label instead -- silently reporting a valid-until-2034
    passport as expired since 2024. Also covers "Dateof Issue" (OCR
    merged the space between "Date" and "of"), which on its own already
    hid the label from an exact substring match."""
    words = [
        OcrWord("Place of Issue", 0.9, ()),
        OcrWord("BHOPAL", 0.9, ()),
        OcrWord("Dateof Issue", 0.85, ()),      # OCR-merged, no space between "Date" and "of"
        OcrWord("Date of Expiry", 0.85, ()),
        OcrWord("03/04/2024", 0.9, ()),
        OcrWord("02/04/2034", 0.9, ()),
    ]
    fields = extract_fields(words)
    assert fields["date_of_issue"].value == "2024-04-03"
    assert fields["date_of_expiry"].value == "2034-04-02"


# ------------------------------------------------------------------ risk ---

def test_realdoc_band_never_reaches_critical():
    huge_fail = Signal(tier=Tier.RULES, check="x", severity=Severity.FAIL, weight=999, message="m")
    verdict = fuse_realdoc([huge_fail], steps=[], insufficient_evidence=False)
    assert verdict.band != "CRITICAL"
    assert verdict.band == "HIGH"


def test_insufficient_evidence_forces_review_regardless_of_score():
    verdict = fuse_realdoc([], steps=[LadderStep("x", "REVIEW")], insufficient_evidence=True)
    assert verdict.band == "REVIEW"


def test_no_findings_is_low():
    verdict = fuse_realdoc([], steps=[], insufficient_evidence=False)
    assert verdict.band == "LOW"


# --------------------------------------------------------- page cropping ---

def test_page_crop_finds_a_document_on_a_contrasting_background():
    """A document photographed on a larger, plainer background (light page
    around a smaller, texturally distinct document) should be cropped
    tighter -- the real-passport case this was built for happened not to
    have this shape (the page already IS approximately the document, see
    README.md), so this proves the mechanism on a case that does."""
    page = np.full((800, 600, 3), 230, dtype=np.uint8)
    doc_region = np.random.RandomState(0).randint(0, 80, (400, 300, 3), dtype=np.uint8)
    page[200:600, 150:450] = doc_region
    cropped = try_crop_to_document(page)
    assert cropped.shape[0] < page.shape[0] or cropped.shape[1] < page.shape[1]


def test_page_crop_is_a_no_op_when_no_confident_boundary_exists():
    """A uniform image (nothing document-shaped to find) must come back
    unchanged, not some arbitrary/degenerate crop."""
    flat = np.full((400, 300, 3), 128, dtype=np.uint8)
    result = try_crop_to_document(flat)
    assert result.shape == flat.shape


def test_mrz_robust_matches_plain_result_when_cropping_does_not_apply():
    """On an image with no crop opportunity, the robust wrapper must
    behave exactly like the underlying try_read_mrz -- no silent behavior
    change for the common case where cropping isn't relevant."""
    blank = np.full((900, 700, 3), 255, dtype=np.uint8)
    plain = mrz_scan.try_read_mrz(cv2.cvtColor(blank, cv2.COLOR_BGR2GRAY))
    robust = mrz_scan.try_read_mrz_robust(blank)
    assert robust.status == plain.status
