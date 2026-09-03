"""Controlled forgery attacks against our own generated documents, each
paired with a pixel-exact ground-truth mask. Tonight ships attack A only
(DOB modification); B-E (portrait replacement, screen recapture, face
mismatch, expiry) land on day 2 per the plan -- this module is structured
so they slot in as additional entries in ATTACKS without touching A.

Every attack function has the same contract:
    (doc_png_path, doc_json_path, rng) -> (forged_image: PIL.Image, mask: np.ndarray uint8, meta: dict)
mask is the same H x W as the document, 255 inside the tampered region, 0
elsewhere -- the ground truth that core/forensics/*.py will be scored
against on day 2.
"""
from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import FONTS, PATHS
from core.fields import PORTRAIT_BBOX, VIZ_CELL_H, VIZ_CELL_W, VIZ_LAYOUT
from core.textgrid import draw_char_grid
from synth.passport import placeholder_portrait


def _blank_mask(size: tuple[int, int]) -> np.ndarray:
    w, h = size
    return np.zeros((h, w), dtype=np.uint8)


def _fill_mask_bbox(mask: np.ndarray, bbox_xyxy: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = bbox_xyxy
    mask[y0:y1, x0:x1] = 255


def attack_dob_modification(doc_png_path: Path, doc_json_path: Path, rng: random.Random
                             ) -> tuple[Image.Image, np.ndarray, dict]:
    """Repaint the VIZ date-of-birth field with a different date. The MRZ
    is left byte-for-byte untouched, so the forged document's own two
    sources of truth -- the printed field and the machine-readable zone --
    now disagree. That disagreement is the whole attack: a forger fixing
    the field a human reads and forgetting the one a machine reads is, per
    the commercial-vendor literature cited in docs/01-RESEARCH.md, the
    single most common real forgery pattern.
    """
    img = Image.open(doc_png_path).convert("RGB")
    truth = json.loads(doc_json_path.read_text())

    bbox = tuple(truth["bboxes"]["date_of_birth"])  # x0, y0, x1, y1
    original_dob = truth["raw_dates"]["date_of_birth"]
    orig_date = dt.date.fromisoformat(original_dob)

    # a different, still-plausible date -- shift the year so it reads
    # naturally rather than looking like random noise in a screenshot
    new_date = orig_date.replace(year=orig_date.year - rng.randint(1, 8))
    new_text = new_date.strftime("%d %b %Y")

    forged = img.copy()
    draw = ImageDraw.Draw(forged)

    # Erase the old text with a solid fill sampled from this SAME bbox's
    # own clean margin (its top few pixels sit above the glyph ink, so
    # they are always background regardless of which field this is or
    # what any neighbouring row contains -- copying a patch from another
    # row was tried first and is wrong: every row has real printed text,
    # so it drags that row's characters into the target field instead of
    # erasing anything). A flat fill instead of the page's true wavy
    # guilloche texture is a visible seam under close inspection -- left
    # deliberately, since a flat retouched patch is itself a realistic
    # forensic tell (see core/forensics/noise.py, day 2), not a flaw to
    # hide.
    x0, y0, x1, y1 = bbox
    bg_strip = np.asarray(img.crop((x0, y0, x1, y0 + 3)))
    bg_color = tuple(int(c) for c in bg_strip.reshape(-1, 3).mean(axis=0))
    draw.rectangle(bbox, fill=bg_color)

    value_font = ImageFont.truetype(FONTS["mono_bold"], 19)
    layout = VIZ_LAYOUT["date_of_birth"]
    draw_char_grid(draw, new_text, x0, y0, VIZ_CELL_W, VIZ_CELL_H, layout["n_cols"],
                    value_font, fill=(20, 24, 34))

    mask = _blank_mask(img.size)
    _fill_mask_bbox(mask, bbox)

    meta = {
        "attack": "A",
        "name": "dob_modification",
        "field": "date_of_birth",
        "original_value": original_dob,
        "forged_value": new_date.isoformat(),
        "bbox": list(bbox),
        "mrz_untouched": True,
        "expected_detection_tier": "rules (cross-zone consistency)",
        # This attack alters the ORIGINAL capture, not a stored record
        # after the fact -- crypto should sign THIS image at intake and
        # verify against that same signature (self-consistency), correctly
        # finding nothing wrong. See core/crypto/manifest.py's docstring.
        "crypto_mode": "self",
    }
    return forged, mask, meta


def attack_portrait_replacement(doc_png_path: Path, doc_json_path: Path, rng: random.Random
                                 ) -> tuple[Image.Image, np.ndarray, dict]:
    """Paste a different identity's photo into the portrait box, with a
    feathered edge (a soft alpha ramp at the seam, not a hard cut) --
    the classic splicing pattern: a competent forger blends the boundary
    rather than leaving a visible rectangle. Detected by photo-region
    statistics (noise/edge-energy discontinuity at the seam) and, if a
    signed manifest is present, by the portrait hash no longer matching
    what was signed -- this is the one attack class where the forensic
    and cryptographic tiers are BOTH expected to fire.

    No real second identity exists yet in data/portraits (none supplied);
    a placeholder generated with a different rng seed stands in, so this
    is a placeholder-vs-placeholder swap until real portraits are added.
    """
    img = Image.open(doc_png_path).convert("RGB")
    truth = json.loads(doc_json_path.read_text())
    bbox = tuple(truth["bboxes"]["portrait"])
    x0, y0, x1, y1 = bbox
    size = (x1 - x0, y1 - y0)

    intruder_seed = rng.randint(10_000, 99_999)
    intruder = placeholder_portrait(size, random.Random(intruder_seed))

    # feather: alpha ramps 0->255 over an 8px border so the seam blends
    # rather than showing a hard rectangle -- realistic splicing, not a
    # strawman easy case
    feather = 8
    mask_alpha = Image.new("L", size, 255)
    md = ImageDraw.Draw(mask_alpha)
    for i in range(feather):
        v = int(255 * i / feather)
        md.rectangle((i, i, size[0] - 1 - i, size[1] - 1 - i), outline=v)
    mask_alpha = mask_alpha.filter(ImageFilter.GaussianBlur(2))

    forged = img.copy()
    forged.paste(intruder, (x0, y0), mask_alpha)

    mask = _blank_mask(img.size)
    _fill_mask_bbox(mask, bbox)

    meta = {
        "attack": "B",
        "name": "portrait_replacement",
        "field": "portrait",
        "original_value": truth.get("portrait_source", "unknown"),
        "forged_value": f"placeholder_seed_{intruder_seed}",
        "bbox": list(bbox),
        "mrz_untouched": True,
        "expected_detection_tier": "forensics (photo region) + crypto (portrait hash)",
        # This attack's whole premise is impersonating an EXISTING signed
        # record with a substituted photo -- verify it against source_doc's
        # own signature, not a fresh signature over the forged image
        # itself (which would trivially match its own tampered pixels).
        "crypto_mode": "impersonation",
    }
    return forged, mask, meta


def attack_screen_recapture(doc_png_path: Path, doc_json_path: Path, rng: random.Random
                             ) -> tuple[Image.Image, np.ndarray, dict]:
    """Simulate presenting the document as a photo of a screen rather than
    the document itself: resolution loss, a real JPEG re-encode (genuine
    quantisation artefacts, not a synthetic stand-in), a sinusoidal moire
    interference pattern from the two pixel grids beating against each
    other, and an uneven glare gradient. This is a whole-document quality
    attack, not a localised edit -- the ground-truth mask is deliberately
    the entire page, matching docs/04-FEATURES.md's own attack table.

    Per docs/01-RESEARCH.md (Third Competition on Document Forgery
    Detection, 2026): composite/recapture attacks are the hardest class in
    the field, for everyone. This one is expected to be caught by forensic
    signals ALONE, with no rules/crosszone violation -- which is exactly
    why the fusion rule caps advisory-only evidence at HIGH/AMBER rather
    than letting it reach RED on its own.
    """
    img = np.asarray(Image.open(doc_png_path).convert("RGB"))
    h, w = img.shape[:2]

    small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    resampled = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    moire_freq = rng.uniform(0.35, 0.55)
    moire = 1.0 + 0.06 * np.sin(xx * moire_freq) * np.sin(yy * moire_freq)
    recaptured = np.clip(resampled.astype(np.float32) * moire[..., None], 0, 255)

    cx, cy = rng.uniform(0.2, 0.8) * w, rng.uniform(0.1, 0.4) * h
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    glare = 30 * np.exp(-(dist ** 2) / (2 * (w * 0.35) ** 2))
    recaptured = np.clip(recaptured + glare[..., None], 0, 255).astype(np.uint8)

    ok, encoded = cv2.imencode(".jpg", cv2.cvtColor(recaptured, cv2.COLOR_RGB2BGR),
                                [cv2.IMWRITE_JPEG_QUALITY, 55])
    recaptured = cv2.cvtColor(cv2.imdecode(encoded, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)

    forged = Image.fromarray(recaptured)
    mask = np.full((h, w), 255, dtype=np.uint8)  # whole-document attack, see docstring

    meta = {
        "attack": "C",
        "name": "screen_recapture",
        "field": None,
        "bbox": [0, 0, w, h],
        "mrz_untouched": False,  # MRZ pixels are degraded too, just not semantically edited
        "expected_detection_tier": "forensics only (no rules/crosszone violation) -- must route to AMBER, never RED",
        "crypto_mode": "self",
    }
    return forged, mask, meta


ATTACKS = {
    "A": attack_dob_modification,
    "B": attack_portrait_replacement,
    "C": attack_screen_recapture,
}


def apply_attack(attack_id: str, doc_id: str, seed: int | None = None) -> tuple[Path, Path, Path]:
    rng = random.Random(seed)
    fn = ATTACKS[attack_id]
    png_path = PATHS["documents"] / f"{doc_id}.png"
    json_path = PATHS["documents"] / f"{doc_id}.json"
    forged_img, mask, meta = fn(png_path, json_path, rng)

    out_dir = PATHS["forged"]
    out_dir.mkdir(parents=True, exist_ok=True)
    forged_path = out_dir / f"forged_{doc_id}_{attack_id}.png"
    mask_path = out_dir / f"mask_{doc_id}_{attack_id}.png"
    meta_path = out_dir / f"forged_{doc_id}_{attack_id}.json"

    forged_img.save(forged_path)
    Image.fromarray(mask).save(mask_path)
    meta["source_doc"] = doc_id
    meta_path.write_text(json.dumps(meta, indent=2))
    return forged_path, mask_path, meta_path


if __name__ == "__main__":
    for attack_id in ATTACKS:
        forged, mask, meta = apply_attack(attack_id, "demo_0001", seed=1)
        print(f"[{attack_id}] wrote {forged}")
