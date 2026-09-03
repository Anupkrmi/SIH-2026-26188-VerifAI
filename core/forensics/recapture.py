"""Screen/print recapture detector: FFT periodic-peak analysis for moire
interference plus a JPEG-blockiness score. Targets synth/forge.py attack
C specifically -- a whole-document quality degradation, not a localised
edit, so this is the one detector expected to fire ALONE on that attack
(no rules/crosszone violation exists for a recapture, by construction).

Per docs/01-RESEARCH.md, this is also the hardest class for the field in
general (the 2026 Third Competition found composite/recapture attacks the
most difficult across both its tracks) -- this module is not claimed to
be a research-grade solution, only a concrete signal against our own
controlled attack.
"""
from __future__ import annotations

import cv2
import numpy as np

from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier

# Calibrated against demo_0001 (genuine moire=1.39/block=0.99, attack C
# moire=1.74/block=1.40). Blockiness shows the larger, more reliable
# separation (a genuine JPEG re-encode leaves a real 8x8 signature); moire
# is kept as a secondary vote. One sample per class -- see docs/06.
MOIRE_RING_THRESHOLD = 1.6
BLOCKINESS_THRESHOLD = 1.15


def _moire_score(gray: np.ndarray) -> float:
    """Ratio of the strongest off-centre FFT magnitude peak (excluding the
    DC/low-frequency core, where a real document's own guilloche pattern
    and printed structure already live) to the spectrum's median -- a
    periodic interference pattern shows up as a sharp, isolated peak well
    above the generally smooth background spectrum."""
    f = np.fft.fftshift(np.fft.fft2(gray.astype(np.float32)))
    mag = np.log1p(np.abs(f))
    h, w = mag.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    ring = mag[(dist > min(h, w) * 0.08) & (dist < min(h, w) * 0.45)]
    if ring.size == 0:
        return 0.0
    return float(ring.max() / (np.median(ring) + 1e-6))


def _blockiness_score(gray: np.ndarray) -> float:
    """Classic JPEG blockiness metric: mean absolute pixel difference
    ACROSS 8x8 block boundaries vs WITHIN blocks. Real re-compression
    (attack C genuinely re-encodes at low JPEG quality) leaves 8x8-aligned
    discontinuities a single clean render does not have."""
    g = gray.astype(np.float32)
    h, w = g.shape
    col_diffs = np.abs(np.diff(g, axis=1))
    row_diffs = np.abs(np.diff(g, axis=0))
    boundary_cols = np.arange(7, w - 1, 8)
    boundary_rows = np.arange(7, h - 1, 8)
    if len(boundary_cols) == 0 or len(boundary_rows) == 0:
        return 1.0
    boundary_energy = col_diffs[:, boundary_cols].mean() + row_diffs[boundary_rows, :].mean()
    interior_energy = col_diffs.mean() + row_diffs.mean()
    return float(boundary_energy / (interior_energy + 1e-6))


def check(gray: np.ndarray, policy: dict | None = None) -> Signal:
    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["capture_anomaly"])

    moire = _moire_score(gray)
    blockiness = _blockiness_score(gray)
    fired = moire > MOIRE_RING_THRESHOLD or blockiness > BLOCKINESS_THRESHOLD

    return Signal(
        tier=Tier.FORENSICS,
        check="recapture_anomaly",
        severity=Severity.FAIL if fired else Severity.PASS,
        weight=weight if fired else 0,
        message=("Capture shows moire/blockiness consistent with a screen or print recapture"
                  if fired else "No screen/print recapture pattern detected"),
        detail={"moire_score": moire, "moire_threshold": MOIRE_RING_THRESHOLD,
                "blockiness_score": blockiness, "blockiness_threshold": BLOCKINESS_THRESHOLD},
    )
