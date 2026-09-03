"""core/face/pipeline.py tests that do NOT require a real human face --
see the module's own docstring for why YuNet correctly detects zero faces
in the procedural placeholder, and why that is an external dependency
(real portraits) rather than a bug to fix here.

These cover the parts that are testable regardless: the quality gate's
own math, and that the pipeline degrades honestly (WEAK, no score) rather
than crashing or guessing when no face is present at all.
"""
import random

import cv2
import numpy as np

from core.face.pipeline import cosine_similarity, quality_gate, verify
from core.types import Severity
from synth.passport import placeholder_portrait


def test_cosine_similarity_uses_a_valid_opencv_distance_constant():
    """Regression test: cv2.FaceRecognizerSF.FR_COSINE (the nested-enum
    spelling, valid on OpenCV 4.x) does not exist on opencv-contrib-python
    5.0.0 -- AttributeError, only ever hit once two real faces both
    cleared the quality gate for the first time in this project's life,
    since every other test here deliberately avoids needing a real face.
    Doesn't need one either: match() just needs two same-shaped feature
    vectors, real biometric content or not."""
    a = np.random.RandomState(0).rand(1, 128).astype(np.float32)
    b = np.random.RandomState(1).rand(1, 128).astype(np.float32)
    assert isinstance(cosine_similarity(a, b), float)


def _placeholder_bgr(seed: int = 1) -> np.ndarray:
    img = placeholder_portrait((280, 280), random.Random(seed))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def test_quality_gate_rejects_a_too_small_face():
    crop = np.full((280, 280, 3), 200, dtype=np.uint8)
    face_row = np.array([0, 0, 30, 30] + [0.0] * 10 + [0.9])  # 30px < MIN_FACE_SIZE
    ok, reason = quality_gate(crop, face_row)
    assert not ok
    assert "too small" in reason


def test_quality_gate_rejects_a_blurred_capture():
    flat = np.full((200, 200, 3), 128, dtype=np.uint8)  # zero-variance -> Laplacian var 0
    face_row = np.array([0, 0, 200, 200] + [0.0] * 10 + [0.9])
    ok, reason = quality_gate(flat, face_row)
    assert not ok
    assert "blurred" in reason


def test_quality_gate_rejects_out_of_range_brightness():
    # a flat-dark image would fail the BLUR gate first (zero variance) --
    # give it real texture (checkerboard) so brightness is the only gate
    # it actually fails, isolating the check under test.
    dark = np.zeros((200, 200, 3), dtype=np.uint8)
    dark[::2, ::2] = 12
    face_row = np.array([0, 0, 200, 200] + [0.0] * 10 + [0.9])
    ok, reason = quality_gate(dark, face_row)
    assert not ok
    assert "brightness" in reason


def test_verify_degrades_honestly_with_no_face_present():
    """The documented, known-empty case: the placeholder has no detectable
    face. verify() must return WEAK with no similarity score attached --
    never a crash, never a guessed number."""
    blank = _placeholder_bgr(1)
    signal = verify(blank, blank)
    assert signal.severity == Severity.WEAK
    assert signal.weight == 0
    assert "similarity" not in signal.detail
