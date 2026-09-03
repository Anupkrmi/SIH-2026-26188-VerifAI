"""Error Level Analysis: included and shown to the jury, and explicitly
labelled untrusted. ELA recompresses the image at a fixed JPEG quality and
diffs against the original; the folklore claim is that edited regions
"stand out" at a different error level. Published forensics literature
does not support this as a reliable signal -- it is highly sensitive to
the image's own prior compression history and produces both false
positives (any high-contrast edge) and false negatives (an edit made
before the image was ever saved as JPEG, as in every attack in this
prototype, which are all edited PNGs). Included on purpose: pre-empting
the "isn't ELA discredited?" question is worth more than the signal
itself. See docs/02-STRATEGY.md.
"""
from __future__ import annotations

import cv2
import numpy as np

from core.types import Severity, Signal, Tier

JPEG_QUALITY = 90


def check(gray: np.ndarray) -> Signal:
    ok, encoded = cv2.imencode(".jpg", gray, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    recompressed = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    diff = cv2.absdiff(gray, recompressed)
    mean_error = float(diff.mean())

    return Signal(
        tier=Tier.FORENSICS,
        check="error_level_analysis",
        severity=Severity.WEAK,  # never PASS/FAIL -- see module docstring
        weight=0,                 # carries no decisive weight, by design
        message=f"ELA mean error level: {mean_error:.2f} (legacy signal, not decisive -- see docs/02-STRATEGY.md)",
        detail={"mean_error": mean_error, "jpeg_quality": JPEG_QUALITY},
    )
