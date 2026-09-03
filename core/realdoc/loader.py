"""Turns whatever the user uploaded (or a path on disk) into a BGR numpy
array Mode B's pipeline can consume. Images go through the same PIL path as
the rest of this project's upload handling (ui/actions.py::cv2_bgr_from_upload);
PDF is rendered via PyMuPDF -- no system Poppler binary needed, unlike
pdf2image -- because real identity/education documents are commonly
PDF scans: both the real passport and the real college ID used to validate
this mode arrived as PDFs, not images, and every college-marksheet PDF
tested was PDF-only with no image alternative.
"""
from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

RENDER_DPI = 200  # enough resolution for OCR/MRZ without excessive memory use


def load_bgr(source: str | Path | bytes, filename_hint: str = "") -> np.ndarray:
    """source: a filesystem path, or raw file bytes (e.g. a Streamlit
    UploadedFile's .getvalue()). filename_hint is only needed when source
    is raw bytes with no path of its own, to tell PDF from image."""
    if isinstance(source, (str, Path)):
        filename_hint = filename_hint or str(source)
        data = Path(source).read_bytes()
    else:
        data = bytes(source)

    if filename_hint.lower().endswith(".pdf"):
        import pymupdf
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            zoom = RENDER_DPI / 72
            pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
        rgb = arr[:, :, :3]  # drop alpha channel if the render produced RGBA
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    pil_img = Image.open(io.BytesIO(data)).convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
