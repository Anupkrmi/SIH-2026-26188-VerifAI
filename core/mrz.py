"""ICAO Doc 9303 TD3 machine-readable zone: build, parse, validate.

Check-digit algorithm (identical for every field and the composite digit):
  value('0'..'9') = 0..9
  value('A'..'Z') = 10..35
  value('<')      = 0
  weights cycle 7, 3, 1, 7, 3, 1, ... starting at the first character
  check digit = (sum of value*weight) mod 10

TD3 layout (2 lines x 44 chars), 0-indexed:
  Line 1
    [0]      document type, 'P'
    [1]      subtype, '<'
    [2:5]    issuing state (3)
    [5:44]   name field: SURNAME<<GIVEN<NAMES, '<'-padded to 39
  Line 2
    [0:9]    passport number, '<'-padded to 9
    [9]      check digit of [0:9]
    [10:13]  nationality (3)
    [13:19]  date of birth, YYMMDD
    [19]     check digit of [13:19]
    [20]     sex: M / F / <
    [21:27]  date of expiry, YYMMDD
    [27]     check digit of [21:27]
    [28:42]  personal number, '<'-padded to 14
    [42]     check digit of [28:42]
    [43]     composite check digit over the 39-char concatenation:
             line2[0:10] + line2[13:20] + line2[21:28] + line2[28:43]
"""
from __future__ import annotations

import datetime as _dt

import cv2
import numpy as np
from pydantic import BaseModel

from config import SEED, MRZ_ROWS, MRZ_COLS  # noqa: F401  (SEED kept for callers wanting determinism)
from core import textgrid

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
_WEIGHTS = (7, 3, 1)


def char_value(c: str) -> int:
    if c == "<":
        return 0
    if c.isdigit():
        return int(c)
    if "A" <= c <= "Z":
        return 10 + (ord(c) - ord("A"))
    raise ValueError(f"character {c!r} is not valid in an MRZ field")


def check_digit(s: str) -> str:
    total = sum(char_value(c) * _WEIGHTS[i % 3] for i, c in enumerate(s))
    return str(total % 10)


# Known, intrinsic blind spot of this scheme (true of the real ICAO
# algorithm, not a defect here): weights 7, 3 and 1 are all coprime with
# 10, so weight * delta === 0 (mod 10) iff delta is itself a multiple of
# 10 -- true for ANY of the three weights and ANY position, including the
# composite digit. A single-character substitution whose value changes by
# exactly 10 (e.g. 'A' value 10 <-> 'K' value 20) is therefore undetectable
# by check digits alone, at that field AND at the composite. Worth stating
# plainly in an audit or a jury Q&A rather than discovering it live.


def _pad(s: str, width: int) -> str:
    s = s.upper().replace(" ", "<")
    if len(s) > width:
        return s[:width]
    return s + "<" * (width - len(s))


def year_from_yy(yy: int, prefer_past: bool) -> int:
    """MRZ dates carry only a 2-digit year. Disambiguating the century is
    inherently heuristic -- real inspection systems use the same trick.
    prefer_past=True (DOB): a birth year is assumed <= this year.
    prefer_past=False (expiry): our demo corpus is generated in the 2020s,
    so we simply assume 2000s. Documented simplification, not a defect."""
    now_yy = _dt.date.today().year % 100
    if prefer_past:
        return 2000 + yy if yy <= now_yy else 1900 + yy
    return 2000 + yy


def _yymmdd(d: _dt.date) -> str:
    return d.strftime("%y%m%d")


class MrzFields(BaseModel):
    document_type: str = "P"
    issuing_state: str
    surname: str
    given_names: str
    passport_number: str
    nationality: str
    date_of_birth: _dt.date
    sex: str  # "M" | "F" | "<"
    date_of_expiry: _dt.date
    personal_number: str = ""


def build_td3(f: MrzFields) -> tuple[str, str]:
    name_field = _pad(f"{f.surname}<<{f.given_names}", 39)
    line1 = "P<" + _pad(f.issuing_state, 3) + name_field
    assert len(line1) == 44, f"line1 length {len(line1)}"

    passport_no = _pad(f.passport_number, 9)
    cd_passport = check_digit(passport_no)
    nationality = _pad(f.nationality, 3)
    dob = _yymmdd(f.date_of_birth)
    cd_dob = check_digit(dob)
    sex = f.sex.upper() if f.sex.upper() in ("M", "F") else "<"
    expiry = _yymmdd(f.date_of_expiry)
    cd_expiry = check_digit(expiry)
    personal_no = _pad(f.personal_number, 14)
    cd_personal = check_digit(personal_no)

    line2 = (
        passport_no + cd_passport + nationality + dob + cd_dob + sex
        + expiry + cd_expiry + personal_no + cd_personal
    )
    composite_input = line2[0:10] + line2[13:20] + line2[21:28] + line2[28:43]
    cd_composite = check_digit(composite_input)
    line2 = line2 + cd_composite
    assert len(line2) == 44, f"line2 length {len(line2)}"
    return line1, line2


class MrzCheck(BaseModel):
    check: str
    expected: str
    found: str
    field: str

    @property
    def ok(self) -> bool:
        return self.expected == self.found


def validate_checkdigits(line2: str) -> list[MrzCheck]:
    """Recompute every check digit from the field it protects and compare
    against the digit actually printed. This is what makes the MRZ
    self-checking: an OCR error or a hand edit that doesn't also fix the
    check digit is caught deterministically, with no model involved."""
    out = []
    passport_no, cd_passport = line2[0:9], line2[9]
    dob, cd_dob = line2[13:19], line2[19]
    expiry, cd_expiry = line2[21:27], line2[27]
    personal_no, cd_personal = line2[28:42], line2[42]
    composite_input = line2[0:10] + line2[13:20] + line2[21:28] + line2[28:43]
    cd_composite = line2[43]

    for field, source, found in [
        ("passport_number", passport_no, cd_passport),
        ("date_of_birth", dob, cd_dob),
        ("date_of_expiry", expiry, cd_expiry),
        ("personal_number", personal_no, cd_personal),
        ("composite", composite_input, cd_composite),
    ]:
        out.append(MrzCheck(check="check_digit", expected=check_digit(source), found=found, field=field))
    return out


def mrz_signals(line2: str, policy: dict | None = None) -> list:
    """validate_checkdigits() results as core.types.Signal objects, ready
    to feed core/risk.py's fusion. Deferred imports: core.types and
    core.rules.engine both sit "above" core.mrz in the dependency graph
    (rules.engine imports MrzFields from here), so importing them at
    module level would cycle."""
    from core.rules.engine import load_policy
    from core.types import Severity, Signal, Tier

    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["mrz_checksum_fail"])
    signals = []
    for c in validate_checkdigits(line2):
        signals.append(Signal(
            tier=Tier.RULES,
            check=f"mrz_checksum_{c.field}",
            severity=Severity.PASS if c.ok else Severity.FAIL,
            weight=0 if c.ok else weight,
            message=(f"MRZ check digit for {c.field} is valid" if c.ok else
                      f"MRZ check digit for {c.field} does not match (expected {c.expected}, found {c.found})"),
        ))
    return signals


def decode_fields(line1: str, line2: str) -> MrzFields:
    """Raw substring extraction + type conversion. Does NOT validate check
    digits -- call validate_checkdigits() separately and decide policy."""
    issuing_state = line1[2:5].replace("<", "")
    name_field = line1[5:44]
    surname, _, given = name_field.partition("<<")
    surname = surname.replace("<", " ").strip()
    given = given.replace("<", " ").strip()

    passport_number = line2[0:9].replace("<", "")
    nationality = line2[10:13].replace("<", "")
    dob_yy, dob_mm, dob_dd = int(line2[13:15]), int(line2[15:17]), int(line2[17:19])
    date_of_birth = _dt.date(year_from_yy(dob_yy, prefer_past=True), dob_mm, dob_dd)
    sex = line2[20]
    exp_yy, exp_mm, exp_dd = int(line2[21:23]), int(line2[23:25]), int(line2[25:27])
    date_of_expiry = _dt.date(year_from_yy(exp_yy, prefer_past=False), exp_mm, exp_dd)
    personal_number = line2[28:42].replace("<", "")

    return MrzFields(
        document_type=line1[0],
        issuing_state=issuing_state,
        surname=surname,
        given_names=given,
        passport_number=passport_number,
        nationality=nationality,
        date_of_birth=date_of_birth,
        sex=sex,
        date_of_expiry=date_of_expiry,
        personal_number=personal_number,
    )


# ------------------------------------------------------------------------
# Reading the MRZ back off pixels: locate the band, split into a 2x44 cell
# grid, match each cell to the cached OCR-A templates (core/glyphs.py) by
# normalised cross-correlation. Because we generate the document ourselves
# in the same font, this is close to exact -- no OCR engine required.
# ------------------------------------------------------------------------

def locate_band(gray: np.ndarray, nominal_bbox: tuple[int, int, int, int] | None = None
                 ) -> tuple[int, int, int, int]:
    """Return (x, y, w, h) of the two-line MRZ band.

    We know the exact placement for every document we generate ourselves
    (synth/passport.py records it in the sidecar JSON) -- pass it as
    nominal_bbox and it is trusted directly (this is the only path Mode A's
    core/pipeline.py ever takes; nothing there calls this fallback).

    Without it (core/realdoc/mrz_scan.py, for arbitrary real documents):
    grow outward from the single densest text row in the bottom 40%,
    capped at a bounded max height, rather than taking every row above a
    loose 30%-of-peak floor. The loose version was measured against a real
    scanned passport PDF (a full page with margin/background around the
    actual data page, not an isolated MRZ) and returned an 869px-tall band
    -- 37% of the page -- because scattered text/watermark/seal density
    throughout the lower page all cleared 30% of the single peak row. A
    real MRZ is two lines of text; it is never a large fraction of a
    properly-oriented page, so the band is bounded accordingly. Confirmed
    against both the synthetic UTO document and a real passport scan.
    """
    if nominal_bbox is not None:
        return nominal_bbox

    h_img, w_img = gray.shape[:2]
    bottom = gray[int(h_img * 0.6):, :]
    _, binary = cv2.threshold(bottom, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    row_ink = binary.sum(axis=1)
    if row_ink.max() == 0:
        raise ValueError("could not locate an MRZ band: no text-density rows found")

    peak = int(row_ink.argmax())
    threshold = row_ink.max() * 0.5
    y0 = peak
    while y0 > 0 and row_ink[y0 - 1] > threshold:
        y0 -= 1
    y1 = peak
    while y1 < len(row_ink) - 1 and row_ink[y1 + 1] > threshold:
        y1 += 1

    max_h = max(1, int(h_img * 0.12))  # 2 lines of MRZ text is never ~more than 12% of a properly-oriented page
    if (y1 - y0 + 1) > max_h:
        pad = max_h // 2
        y0, y1 = max(0, peak - pad), min(len(row_ink) - 1, peak + pad)

    offset = int(h_img * 0.6)
    return (0, offset + y0, w_img, y1 - y0 + 1)


def segment_cells(band: np.ndarray, rows: int = MRZ_ROWS, cols: int = MRZ_COLS
                   ) -> list[list[np.ndarray]]:
    """Split a tightly-cropped band image into an even rows x cols grid.
    Column splitting is shared with the VIZ reader via textgrid.segment_row;
    only the row split (MRZ is always exactly 2 rows) is specific here."""
    h = band.shape[0]
    row_h = h // rows
    return [textgrid.segment_row(band[r * row_h:(r + 1) * row_h, :], cols) for r in range(rows)]


_DIGITS = set("0123456789")

# Columns of line2 known to be digit-only. Two different reasons feed this
# set, kept distinct here for honesty about which is which:
#  - spec-mandated: every check-digit slot is numeric by ICAO construction,
#    and DOB/expiry are always YYMMDD, regardless of issuer.
#  - this issuer's convention: UTO (our own demo generator) always assigns
#    a purely numeric passport number. That is common in the real world
#    but not an ICAO requirement -- a genuine alphanumeric passport number
#    would need this column range left unrestricted.
_SPEC_DIGIT_ONLY = {9, 19, 27, 42, 43} | set(range(13, 19)) | set(range(21, 27))
_ISSUER_DIGIT_ONLY = set(range(0, 9))  # UTO passport_number convention, see above
_LINE2_DIGIT_ONLY_COLUMNS = _SPEC_DIGIT_ONLY | _ISSUER_DIGIT_ONLY

# Glyph matching itself (normalised cross-correlation with an alignment
# search window) is shared with the VIZ reader -- see core/textgrid.py.
match_glyph = textgrid.match_glyph


def read_td3(gray: np.ndarray, nominal_bbox: tuple[int, int, int, int] | None = None
             ) -> tuple[str, str, list[list[float]]]:
    """Read both MRZ lines off a grayscale document image. Returns
    (line1, line2, confidence-grid) where confidence-grid[row][col] is the
    per-cell match score, used by correct_with_checkdigits below."""
    from core.glyphs import get_templates  # deferred: avoids a cv2 import at synth-time

    templates = get_templates()
    x, y, w, h = locate_band(gray, nominal_bbox)
    band = gray[y:y + h, x:x + w]
    grid = segment_cells(band)
    lines: list[str] = []
    confidences: list[list[float]] = []
    for row_idx, row_cells in enumerate(grid):
        chars, confs = [], []
        for col_idx, cell in enumerate(row_cells):
            charset = _DIGITS if (row_idx == 1 and col_idx in _LINE2_DIGIT_ONLY_COLUMNS) else None
            ch, score = match_glyph(cell, templates, charset=charset)
            chars.append(ch)
            confs.append(score)
        lines.append("".join(chars))
        confidences.append(confs)
    return lines[0], lines[1], confidences


_CONFUSION = {"0": "O", "O": "0", "1": "I", "I": "1", "5": "S", "S": "5",
              "8": "B", "B": "8", "2": "Z", "Z": "2"}

# (field name, slice within line2, slice of its check digit)
_CHECKED_FIELDS = [
    ("passport_number", slice(0, 9), slice(9, 10)),
    ("date_of_birth", slice(13, 19), slice(19, 20)),
    ("date_of_expiry", slice(21, 27), slice(27, 28)),
    ("personal_number", slice(28, 42), slice(42, 43)),
]


def correct_with_checkdigits(line2: str, confidences: list[float]) -> tuple[str, list[str]]:
    """Checksum-guided correction: the MRZ charset is closed and every
    field carries a check digit, so an OCR misread can be found and fixed
    by searching the small confusion set until the check digit validates --
    no model, no guessing, just arithmetic. Greedy single-substitution per
    field (the realistic case for a near-exact template reader); a field
    with more than one simultaneous error is reported uncorrected rather
    than exhaustively searched.

    Returns (corrected_line2, list of human-readable correction notes).
    """
    chars = list(line2)
    notes: list[str] = []
    for name, field_slice, cd_slice in _CHECKED_FIELDS:
        field = line2[field_slice]
        cd_found = line2[cd_slice]
        if check_digit(field) == cd_found:
            continue  # already consistent, nothing to correct
        field_start = field_slice.start
        # try one substitution at a time, weakest-confidence position first
        order = sorted(range(len(field)), key=lambda i: confidences[field_start + i])
        for i in order:
            original = field[i]
            for alt in (_CONFUSION.get(original, None),):
                if alt is None:
                    continue
                candidate = field[:i] + alt + field[i + 1:]
                if check_digit(candidate) == cd_found:
                    for j, ch in enumerate(candidate):
                        chars[field_start + j] = ch
                    notes.append(f"{name}: position {i} corrected {original!r} -> {alt!r} (checksum-guided)")
                    break
            else:
                continue
            break
        else:
            notes.append(f"{name}: checksum mismatch, no single-character correction found")
    return "".join(chars), notes
