"""Evidence overlay: box the exact region each FAILED signal is about,
directly on the document image. This is the difference between "the AI
says this is fake" and "the AI found this exact problem" -- see
docs/03-ARCHITECTURE.md, which calls this a must-have for exactly that
reason.

Most detectors don't carry their own bounding box in Signal.detail --
they don't need to, because the regions in question are already known
constants (core/fields.py knows exactly where the portrait and MRZ band
are; core/crosszone.py's check names already encode which VIZ field they
compared). Mapping check name -> region here, rather than pushing a bbox
into every detector's return value, keeps the detectors themselves
free of a UI concern -- correctness of a signal and where to draw it are
different questions.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from config import FONTS
from core.fields import MRZ_BAND_BBOX, PORTRAIT_BBOX, VIZ_LAYOUT
from core.types import Severity, Tier, Verdict

_RED = (226, 86, 79)
_MRZ_BAND_XYXY = (MRZ_BAND_BBOX[0], MRZ_BAND_BBOX[1],
                   MRZ_BAND_BBOX[0] + MRZ_BAND_BBOX[2], MRZ_BAND_BBOX[1] + MRZ_BAND_BBOX[3])

# Tier decisiveness order, matching core/risk.py's fusion hierarchy: when
# more than one signal points at the same region, the label shown is the
# most decisive one's -- crypto outranks a rules violation outranks an
# advisory forensic opinion, exactly as it does in the actual verdict.
_TIER_PRIORITY = {Tier.CRYPTO: 0, Tier.RULES: 1, Tier.FORENSICS: 2, Tier.BIOMETRIC: 3}

_SHORT_LABEL = {
    "photo_region_anomaly": "PORTRAIT",
    "manifest_match": "SIGNATURE",
    "noise_residual_anomaly": "RETOUCHED",
}


def _short_label(check: str) -> str:
    if check in _SHORT_LABEL:
        return _SHORT_LABEL[check]
    if check.startswith("crosszone_"):
        return check[len("crosszone_"):].replace("_", " ").upper()
    if check.startswith("mrz_checksum_"):
        return "MRZ"
    return check.replace("_", " ").upper()


def _bbox_for_signal(check: str, detail: dict) -> tuple[int, int, int, int] | None:
    if check == "photo_region_anomaly":
        return PORTRAIT_BBOX
    if check.startswith("crosszone_"):
        field = check[len("crosszone_"):]
        layout = VIZ_LAYOUT.get(field)
        return tuple(layout["value_bbox"]) if layout else None
    if check.startswith("mrz_checksum_"):
        return _MRZ_BAND_XYXY
    if check == "noise_residual_anomaly":
        x, y, w, h = detail.get("worst_block_xywh", (0, 0, 0, 0))
        return (x, y, x + w, y + h)
    if check == "manifest_match":
        changed = detail.get("changed_fields", [])
        if "portrait_sha256" in changed:
            return PORTRAIT_BBOX
        if "mrz_sha256" in changed:
            return _MRZ_BAND_XYXY
    return None  # recapture_anomaly, ELA: whole-document or non-localised, see overlay()


def overlay(image_path: str, verdict: Verdict) -> Image.Image:
    """Returns a copy of the document with every FAILED signal's region
    boxed and labelled. A whole-document attack (currently: a fired
    recapture_anomaly) draws a full-frame border instead of a box, since
    there is no single region to point at -- that IS the finding.

    Signals are grouped by their RESOLVED bbox, not by check name, before
    drawing anything. An earlier version deduplicated by check name only,
    so attack B -- where photo_region_anomaly (forensics) AND
    manifest_match (crypto) both legitimately point at the portrait --
    drew two labels on top of each other as illegible overlapping text.
    Grouping by bbox and picking the single most decisive signal's label
    (crypto > rules > forensics, see _TIER_PRIORITY) fixes the collision
    at its source and, as a side effect, tells the same story the verdict
    itself does: cryptography's finding is what an officer should read
    first, not a forensic opinion.
    """
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        label_font = ImageFont.truetype(FONTS["sans_bold"], 12)
    except OSError:
        # FONTS["sans_bold"] is a Windows path (config.py) -- doesn't exist
        # on a Linux deploy container. PIL's bitmap default always exists,
        # everywhere; the label text stays readable, just less polished.
        label_font = ImageFont.load_default(size=12)

    whole_document_flagged = False
    groups: dict[tuple[int, int, int, int], list] = {}

    for s in verdict.signals:
        if s.severity != Severity.FAIL:
            continue
        if s.check == "recapture_anomaly":
            whole_document_flagged = True
            continue
        bbox = _bbox_for_signal(s.check, s.detail)
        if bbox is None:
            continue
        groups.setdefault(bbox, []).append(s)

    for bbox, signals in groups.items():
        signals.sort(key=lambda s: _TIER_PRIORITY.get(s.tier, 9))
        primary = signals[0]
        label = _short_label(primary.check)
        if len(signals) > 1:
            label = f"{label} +{len(signals) - 1}"

        x0, y0, x1, y1 = bbox
        draw.rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), outline=_RED, width=3)
        text_bbox = draw.textbbox((0, 0), label, font=label_font)
        tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        bar_h = th + 6

        # A label placed above OR inside the box was tried first and both
        # are wrong for a VIZ field: rows are packed at a 46px pitch with
        # only a 20px gap between them, physically too tight for any
        # floating label to clear the row above without a test-verified
        # collision (tests/test_heatmap.py), and "inside" swallows the
        # very value text the box exists to point at. Placing it to the
        # RIGHT of the box sidesteps the row-pitch constraint entirely --
        # there is nothing else on that row past the value's own width --
        # and is used for every box, not just narrow ones, so there is
        # one code path rather than a size-dependent special case.
        lx = x1 + 6
        ly = y0 - 3 + (y1 - y0 + 6 - bar_h) // 2  # vertically centered on the box
        draw.rectangle((lx, ly, lx + tw + 8, ly + bar_h), fill=_RED)
        draw.text((lx + 4, ly + 3), label, font=label_font, fill=(255, 255, 255))

    if whole_document_flagged:
        w, h = img.size
        draw.rectangle((4, 4, w - 5, h - 5), outline=_RED, width=6)

    return img
