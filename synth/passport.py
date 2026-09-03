"""Generate a fictional TD3 "demo passport": procedural guilloche
background, portrait, VIZ fields, a checksum-valid MRZ, and a permanent
diagonal DEMO watermark. Issuing state UTO is ICAO Doc 9303's own specimen
code, so the output cannot be mistaken for a real country's document.

Every generated document is paired with a sidecar JSON carrying the exact
field values and bounding boxes used to draw it -- that JSON is the ground
truth against which core/mrz.py's pixel reader, core/crosszone.py, and the
day-2 forgery masks are all checked.
"""
from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import DOC_SIZE, DEMO_WATERMARK, FONTS, ISSUING_STATE, PATHS, SEED
from core.fields import (
    MRZ_BAND_BBOX, MRZ_CELL_H, MRZ_CELL_W, PORTRAIT_BBOX, VIZ_CELL_H, VIZ_CELL_W, VIZ_LAYOUT,
)
from core.mrz import MrzFields, build_td3
from core.textgrid import draw_char_grid

_SURNAMES = ["SINGH PALL", "SHARMA", "GURUNG", "THAPA", "RAI", "KHADKA", "SUBBA"]
_GIVEN = ["RAJVEER", "ANANYA", "ARJUN", "PRIYA", "KARAN", "NEHA", "VIKRAM"]


class DocumentFields(MrzFields):
    """MrzFields plus the VIZ-only attributes a real data page shows but the
    MRZ itself does not encode (ICAO Doc 9303 has no issue-date MRZ field)."""
    date_of_issue: dt.date


def random_fields(rng: random.Random) -> DocumentFields:
    dob = dt.date(rng.randint(1970, 2005), rng.randint(1, 12), rng.randint(1, 28))
    issue = dt.date(2024, rng.randint(1, 12), rng.randint(1, 28))
    expiry = dt.date(issue.year + 10, issue.month, issue.day)
    return DocumentFields(
        issuing_state=ISSUING_STATE,
        surname=rng.choice(_SURNAMES),
        given_names=rng.choice(_GIVEN),
        passport_number="".join(rng.choice("0123456789") for _ in range(9)),
        nationality=ISSUING_STATE,
        date_of_birth=dob,
        sex=rng.choice(["M", "F"]),
        date_of_issue=issue,
        date_of_expiry=expiry,
        personal_number="",
    )


def guilloche_background(w: int, h: int, rng: random.Random) -> Image.Image:
    """Cheap procedural stand-in for a security-paper guilloche pattern:
    two interfering sine fields, not a claim of matching a real anti-copy
    pattern. Good enough to read as "official document", which is all the
    demo needs."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f1, f2 = rng.uniform(0.02, 0.04), rng.uniform(0.015, 0.035)
    phase = rng.uniform(0, 2 * np.pi)
    pattern = np.sin(xx * f1 + yy * 0.01 + phase) + np.sin(yy * f2 - xx * 0.008)
    pattern = (pattern - pattern.min()) / (np.ptp(pattern) + 1e-9)
    base = np.array([236, 239, 245], dtype=np.float32)
    line = np.array([198, 208, 224], dtype=np.float32)
    img = base[None, None, :] * (1 - pattern[..., None] * 0.35) + line[None, None, :] * (pattern[..., None] * 0.35)
    return Image.fromarray(img.astype(np.uint8), mode="RGB")


def placeholder_portrait(size: tuple[int, int], rng: random.Random) -> Image.Image:
    """Used only when no real portrait has been supplied yet in
    data/portraits/. Logged, and recorded in the sidecar JSON as
    portrait_source="placeholder" -- never silently presented as real."""
    w, h = size
    img = Image.new("RGB", (w, h), (222, 225, 230))
    d = ImageDraw.Draw(img)
    skin = (int(rng.uniform(180, 220)), int(rng.uniform(140, 180)), int(rng.uniform(120, 160)))
    d.ellipse((w * 0.2, h * 0.12, w * 0.8, h * 0.75), fill=skin, outline=(90, 70, 60))
    eye_y = h * 0.38
    d.ellipse((w * 0.32, eye_y, w * 0.40, eye_y + h * 0.05), fill=(40, 30, 25))
    d.ellipse((w * 0.60, eye_y, w * 0.68, eye_y + h * 0.05), fill=(40, 30, 25))
    d.line((w * 0.42, h * 0.58, w * 0.58, h * 0.58), fill=(120, 60, 55), width=3)
    d.rectangle((0, 0, w - 1, h - 1), outline=(120, 120, 120))
    return img


def _cover_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize preserving aspect ratio until `img` fully covers `size`, then
    center-crop to it exactly -- unlike a blind .resize(), this never
    distorts a real photo's proportions. A real portrait almost never
    arrives already in the portrait box's own aspect ratio (webcam/phone
    photos are landscape or square), and a stretched face measurably
    shrinks YuNet's detected bbox on its squeezed axis: found by actually
    running a real supplied photo end to end -- a 1280x720 frame blindly
    resized into the 220x280 portrait box produced a 47x90 face detection
    (width crushed under quality_gate's 60px floor) although the same
    photo's own raw frame detected a clean 209px-wide face.
    """
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = round(src_w * scale), round(src_h * scale)
    resized = img.resize((new_w, new_h))
    left, top = (new_w - target_w) // 2, (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def _load_or_placeholder_portrait(size: tuple[int, int], rng: random.Random) -> tuple[Image.Image, str]:
    candidates = sorted(PATHS["portraits"].glob("*.jpg")) + sorted(PATHS["portraits"].glob("*.png"))
    if candidates:
        path = rng.choice(candidates)
        img = _cover_resize(Image.open(path).convert("RGB"), size)
        return img, f"user_supplied:{path.name}"
    print("[synth.passport] WARNING: no files in data/portraits/ -- using a "
          "procedural placeholder face. Add real portraits before the "
          "biometric-tier demo needs them.")
    return placeholder_portrait(size, rng), "placeholder"


def _draw_mrz_line(draw: ImageDraw.ImageDraw, line: str, row: int, font: ImageFont.FreeTypeFont) -> None:
    x0, y0, _, _ = MRZ_BAND_BBOX
    y = y0 + row * MRZ_CELL_H
    for col, ch in enumerate(line):
        cell_x = x0 + col * MRZ_CELL_W
        bbox = draw.textbbox((0, 0), ch, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cx = cell_x + (MRZ_CELL_W - w) // 2 - bbox[0]
        cy = y + (MRZ_CELL_H - h) // 2 - bbox[1]
        draw.text((cx, cy), ch, font=font, fill=(20, 20, 20))


def _draw_watermark(img: Image.Image) -> Image.Image:
    """Sparse and light: this must read as an intentional demo marking,
    not as noise fighting the portrait and MRZ for attention.

    Explicitly excluded from the MRZ band and every VIZ value field: a
    watermark stroke alpha-blended over real ink shifts that pixel's own
    colour toward the watermark's, which (a tint-detection pass tried
    first, and this is the reason it was abandoned) is indistinguishable
    from genuine reddish ink without also knowing which pixels the
    watermark touched -- recoverable in principle by inverting the known
    alpha blend, not worth the complexity here. Real specimen/demo
    watermarks are placed to avoid the data-bearing zones for exactly
    this reason: the marking should not compete with the document's own
    machine-readable content. The holes are punched AFTER rotation, in
    the same axis-aligned coordinate frame as the base image (rotate is
    called with expand=False, so the canvas frame does not move).
    """
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    font = ImageFont.truetype(FONTS["sans_bold"], 30)
    text = DEMO_WATERMARK
    w, h = img.size
    for y in range(-h, h * 2, 170):
        for x in range(-w, w * 2, 520):
            d.text((x, y), text, font=font, fill=(180, 30, 30, 38))
    overlay = overlay.rotate(-28, expand=False)

    protect = ImageDraw.Draw(overlay)
    mx, my, mw, mh = MRZ_BAND_BBOX
    protect.rectangle((mx, my, mx + mw, my + mh), fill=(0, 0, 0, 0))
    for layout in VIZ_LAYOUT.values():
        protect.rectangle(layout["value_bbox"], fill=(0, 0, 0, 0))

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def render_document(fields: DocumentFields, rng: random.Random) -> tuple[Image.Image, dict]:
    w, h = DOC_SIZE
    img = guilloche_background(w, h, rng)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(FONTS["sans_bold"], 30)
    sub_font = ImageFont.truetype(FONTS["sans"], 16)
    label_font = ImageFont.truetype(FONTS["sans"], 13)
    value_font = ImageFont.truetype(FONTS["mono_bold"], 19)
    mrz_font = ImageFont.truetype(FONTS["mrz"], 30)

    draw.text((60, 24), "UTOPIA", font=title_font, fill=(20, 30, 60))
    draw.text((60, 60), "DEMONSTRATION PASSPORT  ·  PASSEPORT DE DEMONSTRATION", font=sub_font, fill=(60, 70, 90))
    draw.line((60, 100, w - 60, 100), fill=(150, 160, 180), width=2)

    portrait_size = (PORTRAIT_BBOX[2] - PORTRAIT_BBOX[0], PORTRAIT_BBOX[3] - PORTRAIT_BBOX[1])
    portrait, portrait_source = _load_or_placeholder_portrait(portrait_size, rng)
    img.paste(portrait, (PORTRAIT_BBOX[0], PORTRAIT_BBOX[1]))
    draw.rectangle(PORTRAIT_BBOX, outline=(40, 40, 40), width=2)

    # Uppercase to match what draw_char_grid actually renders (and how real
    # passport VIZ fields are printed) -- the ground truth must record what
    # is on the page, not a prettier string we never drew.
    viz_values = {
        "surname": fields.surname.upper(),
        "given_names": fields.given_names.upper(),
        "passport_number": fields.passport_number.upper(),
        "nationality": fields.nationality.upper(),
        "date_of_birth": fields.date_of_birth.strftime("%d %b %Y").upper(),
        "sex": fields.sex.upper(),
        "date_of_issue": fields.date_of_issue.strftime("%d %b %Y").upper(),
        "date_of_expiry": fields.date_of_expiry.strftime("%d %b %Y").upper(),
    }
    for key, layout in VIZ_LAYOUT.items():
        draw.text(layout["label_pos"], layout["label"], font=label_font, fill=(110, 118, 130))
        x0, y0, _, _ = layout["value_bbox"]
        draw_char_grid(draw, viz_values[key], x0, y0, VIZ_CELL_W, VIZ_CELL_H,
                        layout["n_cols"], value_font, fill=(20, 24, 34))

    line1, line2 = build_td3(fields)
    _draw_mrz_line(draw, line1, 0, mrz_font)
    _draw_mrz_line(draw, line2, 1, mrz_font)

    img = _draw_watermark(img)

    ground_truth = {
        "issuing_state": fields.issuing_state,
        "fields": {**{k: v for k, v in viz_values.items()}, "mrz_line1": line1, "mrz_line2": line2},
        "raw_dates": {
            "date_of_birth": fields.date_of_birth.isoformat(),
            "date_of_issue": fields.date_of_issue.isoformat(),
            "date_of_expiry": fields.date_of_expiry.isoformat(),
        },
        "bboxes": {
            "portrait": list(PORTRAIT_BBOX),
            "mrz_band_xywh": list(MRZ_BAND_BBOX),
            **{k: list(v["value_bbox"]) for k, v in VIZ_LAYOUT.items()},
        },
        "portrait_source": portrait_source,
        "watermark": DEMO_WATERMARK,
    }
    return img, ground_truth


def generate(doc_id: str, fields: DocumentFields | None = None, seed: int | None = None
             ) -> tuple[Path, Path]:
    rng = random.Random(seed if seed is not None else SEED)
    fields = fields or random_fields(rng)
    img, ground_truth = render_document(fields, rng)

    out_dir = PATHS["documents"]
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"{doc_id}.png"
    json_path = out_dir / f"{doc_id}.json"
    img.save(png_path)
    ground_truth["doc_id"] = doc_id
    json_path.write_text(json.dumps(ground_truth, indent=2))
    return png_path, json_path


if __name__ == "__main__":
    png, meta = generate("demo_0001", seed=SEED)
    print(f"wrote {png}")
    print(f"wrote {meta}")
