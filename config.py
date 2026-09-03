"""Single source of truth for paths, seeds and thresholds.

Rule (see CLAUDE.md / plan): nothing else in this repo hardcodes a path or a
magic constant. Every module imports from here.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths ---
ROOT = Path(__file__).resolve().parent

PATHS = {
    "root": ROOT,
    "models": ROOT / "models",
    "data": ROOT / "data",
    "portraits": ROOT / "data" / "portraits",
    "documents": ROOT / "data" / "documents",       # generated genuine docs
    "forged": ROOT / "data" / "forged",             # generated attacks
    "pki": ROOT / "data" / "pki",                   # demo signing authority
    "results": ROOT / "results",
    "cases": ROOT / "results" / "cases",
    "core": ROOT / "core",
    "policy": ROOT / "core" / "rules" / "policy.yaml",
}
for _p in PATHS.values():
    if _p.suffix == "":  # directories only, not the policy.yaml file
        _p.mkdir(parents=True, exist_ok=True)

MODEL_FILES = {
    "yunet": PATHS["models"] / "face_detection_yunet_2023mar.onnx",
    "sface": PATHS["models"] / "face_recognition_sface_2021dec.onnx",
    "glyphs": PATHS["models"] / "mrz_glyphs.npz",
    "viz_glyphs": PATHS["models"] / "viz_glyphs.npz",
}

FONTS = {
    "mrz": r"C:\Windows\Fonts\OCRAEXT.TTF",   # OCR-A Extended: real MRZ-family font
    "sans": r"C:\Windows\Fonts\arial.ttf",
    "sans_bold": r"C:\Windows\Fonts\arialbd.ttf",
    "mono_bold": r"C:\Windows\Fonts\consolab.ttf",  # VIZ field values -- see core/fields.py
}

# --------------------------------------------------------------- seeds ---
SEED = 42

# ----------------------------------------------------------- document ---
DOC_SIZE = (1000, 700)          # px, landscape TD3 data page
ISSUING_STATE = "UTO"           # ICAO Doc 9303 specimen code — never a real country
DEMO_WATERMARK = "DEMO \u2014 NOT A TRAVEL DOCUMENT"

MRZ_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
MRZ_ROWS = 2
MRZ_COLS = 44                   # TD3

# ------------------------------------------------------------- risk ------
# Additive weights. Loaded by core/rules/engine.py from policy.yaml at
# runtime; kept here too as the documented default / fallback.
RISK_BANDS = [
    (0, 25, "LOW", "No action required"),
    (26, 50, "MEDIUM", "Routine review"),
    (51, 75, "HIGH", "Secondary inspection recommended"),
    (76, 100, "CRITICAL", "Secondary inspection recommended"),
]
# NB: language rule — even CRITICAL never accuses. See core/risk.py.

FACE_MATCH_COSINE_THRESHOLD = None  # measured on day 3, written to results/face_threshold.json
