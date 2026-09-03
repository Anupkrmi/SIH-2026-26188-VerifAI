"""core/forensics/heatmap.py acceptance tests: the box actually lands on
the region the failing signal is about, and a clean document gets no
boxes at all -- run against the real Attack Wall corpus, not synthetic
Signal objects, since the whole point is the mapping from a real check
name to a real bbox.
"""
import numpy as np
import pytest
from PIL import Image

from config import PATHS
from core.fields import VIZ_LAYOUT
from core.forensics.heatmap import overlay
from core.pipeline import screen_document

GENUINE = PATHS["documents"] / "demo_0001.png"
ATTACK_A = PATHS["forged"] / "forged_demo_0001_A.png"

pytestmark = pytest.mark.skipif(
    not GENUINE.exists(), reason="run `python -m synth.passport && python -m synth.forge` first"
)

_RED = np.array([226, 86, 79])


def _has_red_pixel(img: Image.Image, bbox_xyxy) -> bool:
    x0, y0, x1, y1 = bbox_xyxy
    region = np.asarray(img)[max(0, y0 - 5):y1 + 5, max(0, x0 - 5):x1 + 5]
    dist = np.abs(region.astype(int) - _RED).sum(axis=-1)
    return bool((dist < 20).any())


def test_genuine_document_gets_no_boxes():
    verdict, _ = screen_document(GENUINE)
    original = np.asarray(Image.open(GENUINE).convert("RGB"))
    annotated = np.asarray(overlay(str(GENUINE), verdict))
    assert original.shape == annotated.shape
    assert np.array_equal(original, annotated), "a clean document must come back pixel-identical"


def test_dob_forgery_boxes_the_date_of_birth_field():
    verdict, _ = screen_document(ATTACK_A)
    annotated = overlay(str(ATTACK_A), verdict)
    dob_bbox = tuple(VIZ_LAYOUT["date_of_birth"]["value_bbox"])
    assert _has_red_pixel(annotated, dob_bbox)


def test_dob_forgery_does_not_box_unrelated_regions():
    """The nationality field passed its crosszone check -- it must not
    get a box just because SOMETHING on the document failed."""
    verdict, _ = screen_document(ATTACK_A)
    annotated = overlay(str(ATTACK_A), verdict)
    nationality_bbox = tuple(VIZ_LAYOUT["nationality"]["value_bbox"])
    assert not _has_red_pixel(annotated, nationality_bbox)


def test_overlay_preserves_image_size():
    verdict, _ = screen_document(ATTACK_A)
    original = Image.open(ATTACK_A)
    annotated = overlay(str(ATTACK_A), verdict)
    assert annotated.size == original.size
