"""General block-level residual anomaly detector: img minus a median-blur
of itself leaves a noise/texture residual. The first version of this
module compared each block's residual variance against the WHOLE page's
distribution and never fired: this document's guilloche background is
naturally very smooth almost everywhere, so a locally-flat retouched patch
(synth/forge.py attack A's flat-fill erasure) was no flatter than plenty
of genuine background already was, in *global* terms -- see docs/06 for
the calibration run that caught this.

The fix compares each block against its own LOCAL neighbourhood instead of
the whole page: a patch that is anomalously flat relative to what
immediately surrounds it is suspicious regardless of how flat the page is
somewhere else entirely. This is what "locally inconsistent" should have
meant from the start.

Deliberately general rather than field-targeted: unlike photo_region.py
(which knows exactly where the portrait is), this scans the whole page in
blocks and flags whichever one deviates most from its neighbours. It is
what would eventually catch an edit whose location isn't already known.

Known limitation, stated rather than hidden: this does not currently
catch synth/forge.py's attack A. That erasure fills its entire 26px-tall
field with new text edge-to-edge, leaving almost no exposed flat margin
for a residual detector to find -- the forger's redraw is, for this
specific signal, well executed. Attack A is instead caught instantly by
core/crosszone.py (the printed date and the MRZ date disagree). That is
not a gap in this module so much as the actual argument for the Trust
Ladder: no single forensic trick is expected to catch everything, which is
why signals are layered rather than relying on any one of them alone.
"""
from __future__ import annotations

import cv2
import numpy as np

from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier

BLOCK = 24
NEIGHBORHOOD = 2  # blocks in each direction; a 5x5 window around each candidate
Z_THRESHOLD = 2.0  # calibrated against demo_0001 genuine vs attack A, see docs/06


def _block_residual_variances(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    residual = gray.astype(np.float32) - cv2.medianBlur(gray, 5).astype(np.float32)
    h, w = gray.shape[:2]
    rows, cols = h // BLOCK, w // BLOCK
    variances = np.zeros((rows, cols), dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            block = residual[r * BLOCK:(r + 1) * BLOCK, c * BLOCK:(c + 1) * BLOCK]
            variances[r, c] = block.var()
    return variances, rows, cols


def _local_z_scores(variances: np.ndarray) -> np.ndarray:
    rows, cols = variances.shape
    z = np.zeros_like(variances)
    n = NEIGHBORHOOD
    for r in range(rows):
        for c in range(cols):
            r0, r1 = max(0, r - n), min(rows, r + n + 1)
            c0, c1 = max(0, c - n), min(cols, c + n + 1)
            window = variances[r0:r1, c0:c1]
            mean, std = window.mean(), window.std() + 1e-6
            z[r, c] = (variances[r, c] - mean) / std
    return z


def check(gray: np.ndarray, exclude_bbox_xywh: tuple[int, int, int, int] | None = None,
          policy: dict | None = None) -> Signal:
    """exclude_bbox_xywh: a region to skip (e.g. the MRZ band, which is
    dense text and has a legitimately different residual profile from
    blank background -- excluding it avoids a false positive there)."""
    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["photo_anomaly"])  # same category as photo_region

    variances, rows, cols = _block_residual_variances(gray)

    if exclude_bbox_xywh is not None:
        ex, ey, ew, eh = exclude_bbox_xywh
        r0, r1 = ey // BLOCK, (ey + eh) // BLOCK + 1
        c0, c1 = ex // BLOCK, (ex + ew) // BLOCK + 1
        variances[r0:r1, c0:c1] = np.nan  # excluded from both scoring AND neighbourhoods

    valid = ~np.isnan(variances)
    z_scores = np.zeros_like(variances)
    z_scores[valid] = _local_z_scores(np.where(valid, variances, np.nanmean(variances)))[valid]

    worst_idx = np.unravel_index(np.argmin(np.where(valid, z_scores, 0)), z_scores.shape)
    worst_z = float(z_scores[worst_idx])
    worst_bbox = (worst_idx[1] * BLOCK, worst_idx[0] * BLOCK, BLOCK, BLOCK)

    ok = worst_z > -Z_THRESHOLD
    return Signal(
        tier=Tier.FORENSICS,
        check="noise_residual_anomaly",
        severity=Severity.PASS if ok else Severity.FAIL,
        weight=0 if ok else weight,
        message=("No anomalously flat (retouched-looking) region detected" if ok
                  else f"An unusually flat, low-texture patch was found at pixel {worst_bbox} "
                       f"-- consistent with a retouched or pasted region"),
        detail={"worst_z_score": worst_z, "threshold": -Z_THRESHOLD, "worst_block_xywh": list(worst_bbox)},
    )
