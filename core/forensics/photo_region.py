"""Photo-region tamper check: the primary forensic signal, per
docs/03-ARCHITECTURE.md's own ordering.

We know the portrait's exact bounding box (core/fields.py), so this is a
targeted check, not a general splicing detector: a genuine portrait has
roughly uniform local sharpness across its whole area, because it is one
photograph. A pasted portrait blended with a feathered edge (the technique
synth/forge.py's attack B actually uses) locally SMOOTHS the boundary ring
relative to the interior -- the alpha ramp is, by construction, a blur.
That ring-vs-interior sharpness ratio is what this module measures.
"""
from __future__ import annotations

import cv2
import numpy as np

from core.fields import PORTRAIT_BBOX
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier

RING_WIDTH = 6
# Recalibrated 2026-08-28 after the first real (non-placeholder) portrait
# was supplied: the original 0.90 was fit to the procedural placeholder
# oval alone (genuine/attack A scored 0.983 there -- a flat, near-uniform
# drawing keeps ring and interior sharpness almost identical). A real
# photograph does not: its rim (hair/shoulder/background) is naturally
# less textured than its interior (eyes, glasses, facial detail), which
# drags genuine's own ratio down to ~0.75 -- comfortably above the old
# threshold's failure mode caught here (real photo genuine scored 0.75 and
# FAILED against 0.90). Re-measured against demo_0001 with the real
# portrait baked in: genuine 0.750, attack A 0.750 (portrait untouched,
# correctly identical to genuine), attack B (real photo swap) 0.112,
# attack C 1.670. Still one real sample per class, not a statistically
# validated threshold -- see docs/06 -- but the genuine/attack-B gap
# (0.750 vs 0.112) has wide margin either side of 0.40.
RATIO_THRESHOLD = 0.40


def _laplacian_variance(patch: np.ndarray) -> float:
    if patch.size == 0:
        return 0.0
    return float(cv2.Laplacian(patch, cv2.CV_64F).var())


def _ring_and_interior(gray: np.ndarray, bbox_xyxy: tuple[int, int, int, int]
                        ) -> tuple[np.ndarray, np.ndarray]:
    x0, y0, x1, y1 = bbox_xyxy
    region = gray[y0:y1, x0:x1]
    h, w = region.shape[:2]
    r = RING_WIDTH
    ring_mask = np.zeros((h, w), dtype=bool)
    ring_mask[:r, :] = ring_mask[-r:, :] = True
    ring_mask[:, :r] = ring_mask[:, -r:] = True
    interior_mask = ~ring_mask
    return region[ring_mask], region[interior_mask]


def check(gray: np.ndarray, bbox_xyxy: tuple[int, int, int, int] = PORTRAIT_BBOX,
          policy: dict | None = None) -> Signal:
    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["photo_anomaly"])

    x0, y0, x1, y1 = bbox_xyxy
    region = gray[y0:y1, x0:x1]
    ring_pixels, interior_pixels = _ring_and_interior(gray, bbox_xyxy)

    # Laplacian variance needs 2D structure; recompute on the full region
    # for the interior/ring by masking rather than flattening, so edge
    # operators see real neighbourhoods rather than a 1-D pixel list.
    h, w = region.shape[:2]
    r = RING_WIDTH
    interior_patch = region[r:h - r, r:w - r] if h > 2 * r and w > 2 * r else region
    lap_full = _laplacian_variance(region)
    lap_interior = _laplacian_variance(interior_patch)

    ring_energy = float(np.var(ring_pixels)) if ring_pixels.size else 0.0
    interior_energy = float(np.var(interior_pixels)) if interior_pixels.size else 1e-6
    # ratio of the BOUNDARY ring's own local sharpness (Laplacian on a thin
    # band, approximated via the full-vs-interior-only Laplacian delta)
    # against the interior's -- a genuine single-source photo keeps these
    # close; a feathered paste seam suppresses the ring's high frequencies.
    ratio = (lap_full - lap_interior) / (lap_interior + 1e-6) if lap_interior > 0 else 1.0
    ratio = abs(ratio)

    ok = ratio >= RATIO_THRESHOLD or lap_interior < 1e-6
    return Signal(
        tier=Tier.FORENSICS,
        check="photo_region_anomaly",
        severity=Severity.PASS if ok else Severity.FAIL,
        weight=0 if ok else weight,
        message=("Portrait boundary sharpness is consistent with a single-source photograph" if ok
                  else "Portrait boundary shows a smoothed seam consistent with a pasted/blended photo"),
        detail={"ring_interior_ratio": ratio, "threshold": RATIO_THRESHOLD,
                "lap_full": lap_full, "lap_interior": lap_interior,
                "ring_pixel_variance": ring_energy, "interior_pixel_variance": interior_energy},
    )
