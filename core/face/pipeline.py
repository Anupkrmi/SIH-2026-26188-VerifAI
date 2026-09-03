"""Face verification: YuNet detection, a quality gate that runs BEFORE any
match score is produced, SFace embedding, cosine similarity.

Order matters and is enforced by returning early: a match score computed
on a bad capture is worse than no score at all, so a failed quality gate
returns REVIEW with no similarity number attached, never a low-confidence
guess. See docs/03-ARCHITECTURE.md Module 4.

Known limitation, stated plainly: end-to-end detection needs a real human
face. The placeholder faces synth/passport.py falls back to when
data/portraits/ is empty are simple procedural drawings (an oval, two
dots, a line) with none of the statistical structure YuNet was trained on
-- it correctly detects zero faces in them, every time. That is not a bug
in this module; it is why the plan calls for two real, consenting
portraits before this tier can be demonstrated live. Everything below is
written and unit-tested against that eventuality, not against the
placeholder.
"""
from __future__ import annotations

import cv2
import numpy as np

from config import MODEL_FILES
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier

MIN_FACE_SIZE = 60          # px, shorter side of the detected face box
BLUR_VARIANCE_MIN = 40.0    # Laplacian variance floor
BRIGHTNESS_RANGE = (40, 220)  # mean grayscale intensity, acceptable band

_detector = None
_recognizer = None


def _get_detector(input_size: tuple[int, int]) -> cv2.FaceDetectorYN:
    global _detector
    if _detector is None:
        _detector = cv2.FaceDetectorYN.create(str(MODEL_FILES["yunet"]), "", input_size,
                                                score_threshold=0.7, nms_threshold=0.3, top_k=10)
    else:
        _detector.setInputSize(input_size)
    return _detector


def _get_recognizer() -> cv2.FaceRecognizerSF:
    global _recognizer
    if _recognizer is None:
        _recognizer = cv2.FaceRecognizerSF.create(str(MODEL_FILES["sface"]), "")
    return _recognizer


def detect_largest_face(bgr: np.ndarray) -> np.ndarray | None:
    """Returns the single highest-confidence YuNet detection as a 15-value
    row (bbox x,y,w,h + 5 landmark pairs + score), or None."""
    h, w = bgr.shape[:2]
    detector = _get_detector((w, h))
    _, faces = detector.detect(bgr)
    if faces is None or len(faces) == 0:
        return None
    return faces[np.argmax(faces[:, -1])]


def detect_faces(bgr: np.ndarray) -> np.ndarray:
    """Every YuNet detection on the image (same 15-value row shape as
    detect_largest_face), not reduced to the single best one. Added for
    core/realdoc/portrait.py, which scores multiple candidates on an
    arbitrary document page to find the most plausible portrait region --
    detect_largest_face's single-best reduction is right everywhere else in
    this project (a live capture or a known portrait crop has exactly one
    face to find) and is left untouched."""
    h, w = bgr.shape[:2]
    detector = _get_detector((w, h))
    _, faces = detector.detect(bgr)
    return faces if faces is not None else np.empty((0, 15), dtype=np.float32)


def quality_gate(bgr: np.ndarray, face_row: np.ndarray) -> tuple[bool, str]:
    x, y, w, h = face_row[:4].astype(int)
    x, y = max(0, x), max(0, y)
    crop = bgr[y:y + h, x:x + w]
    if crop.size == 0 or min(w, h) < MIN_FACE_SIZE:
        return False, f"detected face is too small ({min(w, h)}px, need >= {MIN_FACE_SIZE}px)"

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < BLUR_VARIANCE_MIN:
        return False, f"capture is too blurred (sharpness {blur:.1f}, need >= {BLUR_VARIANCE_MIN})"

    brightness = gray.mean()
    lo, hi = BRIGHTNESS_RANGE
    if not (lo <= brightness <= hi):
        return False, f"capture brightness out of range ({brightness:.0f}, need {lo}-{hi})"

    return True, "quality gate passed"


def embed(bgr: np.ndarray, face_row: np.ndarray) -> np.ndarray:
    recognizer = _get_recognizer()
    aligned = recognizer.alignCrop(bgr, face_row)
    return recognizer.feature(aligned)


def cosine_similarity(feature_a: np.ndarray, feature_b: np.ndarray) -> float:
    recognizer = _get_recognizer()
    # cv2.FaceRecognizerSF.FR_COSINE (the nested-enum spelling, valid on the
    # OpenCV 4.x this was originally written against) was never actually
    # exercised until two real faces both cleared the quality gate for the
    # first time -- opencv-contrib-python 5.0.0's Python bindings flatten
    # it to a module-level name instead. Confirmed against the installed
    # module (dir(cv2.FaceRecognizerSF) no longer lists FR_COSINE at all).
    return float(recognizer.match(feature_a, feature_b, cv2.FaceRecognizerSF_FR_COSINE))


# Placeholder until real portraits let this project measure its own
# threshold and write results/face_threshold.json (see docs/05-EXECUTION.md
# -- "threshold is measured, not assumed"). This exact value is OpenCV
# Zoo's own reference SFace threshold, verified against the source file
# directly (models/face_recognition_sface/sface.py, self._threshold_cosine
# = 0.363), used here only as a documented, cited starting point -- never
# presented as a number this project itself measured until it is.
DEFAULT_MATCH_THRESHOLD = 0.363


def verify(document_bgr: np.ndarray, live_bgr: np.ndarray, policy: dict | None = None,
           threshold: float | None = None) -> Signal:
    """The full Module 4 pipeline: detect -> quality gate -> embed -> match.
    Returns exactly one Signal, biometric tier, ready to feed core/risk.py.
    """
    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["face_mismatch"])
    threshold = threshold if threshold is not None else DEFAULT_MATCH_THRESHOLD

    doc_face = detect_largest_face(document_bgr)
    if doc_face is None:
        return Signal(tier=Tier.BIOMETRIC, check="face_verification", severity=Severity.WEAK, weight=0,
                       message="No face detected in the document portrait -- verification skipped")

    live_face = detect_largest_face(live_bgr)
    if live_face is None:
        return Signal(tier=Tier.BIOMETRIC, check="face_verification", severity=Severity.WEAK, weight=0,
                       message="No face detected in the live capture -- ask for a retake")

    ok_doc, reason_doc = quality_gate(document_bgr, doc_face)
    ok_live, reason_live = quality_gate(live_bgr, live_face)
    if not (ok_doc and ok_live):
        reason = reason_doc if not ok_doc else reason_live
        return Signal(tier=Tier.BIOMETRIC, check="face_verification", severity=Severity.WEAK, weight=0,
                       message=f"Quality gate failed, no match score produced: {reason}")

    similarity = cosine_similarity(embed(document_bgr, doc_face), embed(live_bgr, live_face))
    matched = similarity >= threshold
    return Signal(
        tier=Tier.BIOMETRIC,
        check="face_verification",
        severity=Severity.PASS if matched else Severity.FAIL,
        weight=0 if matched else weight,
        message=(f"Face matches the document portrait (similarity {similarity:.3f} >= {threshold:.3f})"
                  if matched else
                  f"Face does not match the document portrait (similarity {similarity:.3f} < {threshold:.3f})"),
        detail={"similarity": similarity, "threshold": threshold},
    )
