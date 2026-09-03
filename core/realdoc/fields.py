"""Best-effort field extraction from OCR text on an arbitrary real
document: regex/keyword matching over whatever core/realdoc/ocr.py
returned, not a learned extractor. Every field is reported EXTRACTED /
UNCERTAIN / NOT_DETECTED with a confidence bucket -- never a fabricated
value for a field that wasn't actually found.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from core.realdoc.ocr import OcrWord

_MONTHS = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
           "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}

_DATE_PATTERNS = [
    r"\b(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s+(\d{4})\b",
    r"\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b",     # 2004-08-14 (ISO-ish)
    r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b",   # 14/08/2004, 14-08-04
]

_DOC_NUMBER_PATTERN = re.compile(r"\b[A-Z]{0,3}[0-9]{6,12}\b")
# Aadhaar's own universal print format: 12 digits in 3 groups of 4, always
# space-separated ("2878 8883 7088") -- the plain contiguous-digit pattern
# above only ever sees each 4-digit group as its own separate OCR line, so
# a real Aadhaar number was silently never extracted at all. Distinctive
# enough (12 digits, exactly this grouping) to scan for directly across
# every OCR line, independent of finding a label first -- Aadhaar prints
# the number as its own line with no adjacent "NUMBER:" style label.
_AADHAAR_NUMBER_PATTERN = re.compile(r"\b(\d{4})\s(\d{4})\s(\d{4})\b")

_LABEL_HINTS: dict[str, list[str]] = {
    "name": ["NAME", "SURNAME", "GIVEN NAME"],
    # "D0B" (zero, not letter O) is a real, observed OCR misread of "DOB"
    # in a printed Aadhaar's small mixed Hindi/English label -- same idea
    # as core/mrz.py's own _CONFUSION table for exactly this class of
    # character confusion, applied here to a label instead of a checksum.
    "date_of_birth": ["DATE OF BIRTH", "DOB", "D0B", "BIRTH"],
    "document_number": ["PASSPORT NO", "DOCUMENT NO", "ID NO", "REGISTRATION NO",
                          "ROLL NO", "AADHAAR NO", "AADHAARNO", "NUMBER"],
    "date_of_issue": ["DATE OF ISSUE", "ISSUE DATE", "ISSUED"],
    "date_of_expiry": ["DATE OF EXPIRY", "EXPIRY", "VALID UNTIL", "VALID UPTO"],
    "nationality": ["NATIONALITY"],
    "gender": ["SEX", "GENDER"],
    "institution": ["UNIVERSITY", "COLLEGE", "INSTITUTE", "BOARD"],
}
_ALL_FIELD_KEYS = tuple(_LABEL_HINTS.keys())
_GENDER_TOKENS = ("MALE", "FEMALE", "TRANSGENDER", "M", "F")
_ALPHA_RUN = re.compile(r"[A-Z]{2,}")


@dataclass
class ExtractedField:
    value: str
    status: str        # "EXTRACTED" | "UNCERTAIN" | "NOT_DETECTED"
    confidence: str     # "HIGH" | "MEDIUM" | "LOW" | "-"
    source: str = ""    # the OCR line this came from, for audit


def _confidence_bucket(score: float) -> str:
    if score >= 0.85:
        return "HIGH"
    if score >= 0.60:
        return "MEDIUM"
    return "LOW"


def _try_parse_date(text_upper: str) -> str:
    """Returns an ISO date string, or "" if nothing plausible was found."""
    import datetime as _dt
    for pat in _DATE_PATTERNS:
        m = re.search(pat, text_upper)
        if not m:
            continue
        g = m.groups()
        try:
            if g[1] in _MONTHS:
                d, mon, y = int(g[0]), _MONTHS[g[1]], int(g[2])
            elif len(g[0]) == 4:
                y, mon, d = int(g[0]), int(g[1]), int(g[2])
            else:
                d, mon, y = int(g[0]), int(g[1]), int(g[2])
                if y < 100:
                    y += 2000 if y < 50 else 1900
            return _dt.date(y, mon, d).isoformat()
        except ValueError:
            continue
    return ""


def _match_hint(line: str, hints: list[str]) -> tuple[str, str] | None:
    """Match a hint against `line`, tolerating OCR merging adjacent words
    together with no space -- a real passport's "Date of Issue" label was
    read back as "Dateof Issue" (no space between "Date" and "of"),
    silently failing an exact "DATE OF ISSUE" substring check and causing
    the NEXT label's own value to be grabbed instead by the "next line"
    fallback below. Tries the exact form first, then a space-collapsed
    comparison on both sides. Returns (hint, text after it in `line`) in
    whichever form actually matched, or None."""
    hit = next((h for h in hints if h in line), None)
    if hit is not None:
        return hit, line.split(hit, 1)[1]
    compact = line.replace(" ", "")
    for h in hints:
        h_compact = h.replace(" ", "")
        if h_compact in compact:
            idx = compact.index(h_compact) + len(h_compact)
            return h, compact[idx:]
    return None


def _line_matches_any_hint(line: str, hints: list[str]) -> bool:
    return _match_hint(line, hints) is not None


def _is_bare_label_line(line: str) -> bool:
    """True if `line` matches some field's label with nothing left over on
    the same line -- a label printed with no value of its own. Real ID
    layouts commonly stack several such labels consecutively (Date of
    Issue immediately above Date of Expiry, on a real passport), with
    their values printed afterward as their own equal-length block, in
    the same order -- see the block-pairing logic in extract_fields."""
    for hints in _LABEL_HINTS.values():
        found = _match_hint(line, hints)
        if found is not None and len(found[1].strip(" :-")) < 2:
            return True
    return False


def extract_fields(words: list[OcrWord]) -> dict[str, ExtractedField]:
    """One pass over OCR'd lines: find a label keyword, then take the value
    from the remainder of that same line, or the very next line if the
    label line has no residual text -- documents commonly print a label and
    its value as two separately-boxed OCR regions, stacked vertically."""
    lines = [w.text for w in words]
    upper_lines = [l.upper() for l in lines]
    fields: dict[str, ExtractedField] = {}

    all_hints = [h for hints in _LABEL_HINTS.values() for h in hints]

    for i, line in enumerate(upper_lines):
        for field_key, hints in _LABEL_HINTS.items():
            if field_key in fields:
                continue
            found = _match_hint(line, hints)
            if found is None:
                continue
            hit, remainder_raw = found
            remainder = remainder_raw.strip(" :-")
            if len(remainder) >= 2:
                candidate = remainder
            elif _is_bare_label_line(line):
                # This label has no value of its own on the same line.
                # Real ID layouts commonly stack several such labels
                # consecutively (Date of Issue directly above Date of
                # Expiry, confirmed on a real passport), printing ALL
                # their values afterward as an equal-length block in the
                # same order -- NOT one value immediately below each
                # label. A naive "next line" grab silently paired Date of
                # Issue's own value with the Date of Expiry label instead
                # on that passport. Find the full run of consecutive
                # bare-label lines this one sits in, and pair by POSITION
                # within that run against the value-line run immediately
                # following it. Degrades to exactly the old "next line"
                # behaviour when the label isn't part of a stack (a run
                # of length 1).
                block_start = i
                while block_start > 0 and _is_bare_label_line(upper_lines[block_start - 1]):
                    block_start -= 1
                block_end = i
                while block_end + 1 < len(upper_lines) and _is_bare_label_line(upper_lines[block_end + 1]):
                    block_end += 1
                value_idx = block_end + 1 + (i - block_start)
                value_line = upper_lines[value_idx] if value_idx < len(upper_lines) else ""
                candidate = value_line if (value_line and not _line_matches_any_hint(value_line, all_hints)) else ""
            else:
                candidate = ""
            if not candidate:
                continue
            conf = words[i].confidence

            if field_key.startswith("date_of"):
                parsed = _try_parse_date(candidate)
                if parsed:
                    fields[field_key] = ExtractedField(parsed, "EXTRACTED", _confidence_bucket(conf), lines[i])
            elif field_key == "document_number":
                m = _DOC_NUMBER_PATTERN.search(candidate)
                if m:
                    fields[field_key] = ExtractedField(m.group(0), "EXTRACTED", _confidence_bucket(conf), lines[i])
            elif field_key == "gender":
                token = candidate.strip().split()[0] if candidate.strip() else ""
                if token in _GENDER_TOKENS:
                    fields[field_key] = ExtractedField(token, "EXTRACTED", _confidence_bucket(conf), lines[i])
            else:
                # A free-text field (name/nationality/institution) grabbed
                # from a neighbouring OCR box that turns out to be numbers-
                # only (a stray date/ID fragment, the same watermark-driven
                # misread that motivated the gender check above) is reported
                # NOT_DETECTED rather than shown as a bogus "name".
                value = candidate[:60].strip()
                if value and _ALPHA_RUN.search(value):
                    status = "EXTRACTED" if conf >= 0.60 else "UNCERTAIN"
                    fields[field_key] = ExtractedField(value, status, _confidence_bucket(conf), lines[i])
            break

    # Supplementary, label-independent passes: some values are printed in
    # a distinctive enough FORMAT to recognise directly, with no adjacent
    # "LABEL:" text at all -- an Aadhaar card prints "MALE" or "FEMALE"
    # bare (bilingual pair, e.g. "/ MALE"), and its 12-digit number as its
    # own line, both true on the real Aadhaar this was found against.
    if "document_number" not in fields:
        for i, line in enumerate(upper_lines):
            m = _AADHAAR_NUMBER_PATTERN.search(line)
            if m:
                fields["document_number"] = ExtractedField(
                    "".join(m.groups()), "EXTRACTED", _confidence_bucket(words[i].confidence), lines[i])
                break

    if "gender" not in fields:
        # Bare M/F (no adjacent SEX/GENDER label) is excluded here --
        # too easily a false positive (a stray section letter, unit,
        # initial) once nothing anchors it to an actual gender field.
        # Only the unambiguous full words are trusted label-independent.
        for i, line in enumerate(upper_lines):
            tokens = re.findall(r"[A-Z]+", line)
            hit = next((t for t in tokens if t in ("MALE", "FEMALE", "TRANSGENDER")), None)
            if hit:
                fields["gender"] = ExtractedField(hit, "EXTRACTED", _confidence_bucket(words[i].confidence), lines[i])
                break

    # Positional fallback for name: an Indian ID card conventionally prints
    # the holder's name directly above their date of birth, with no "NAME:"
    # label of its own at all (confirmed against a real Aadhaar -- the name
    # appeared twice, neither time next to a label). Only applied once a
    # DOB was actually found, and only if the candidate line looks like a
    # plausible name (2-4 alphabetic words, not itself another field's
    # label) -- reported UNCERTAIN, never EXTRACTED, because this is
    # positional inference, not a labelled read.
    dob_field = fields.get("date_of_birth")
    if "name" not in fields and dob_field is not None and dob_field.status != "NOT_DETECTED":
        try:
            dob_idx = lines.index(dob_field.source)
        except ValueError:
            dob_idx = -1
        if dob_idx > 0:
            candidate = lines[dob_idx - 1].strip()
            candidate_words = candidate.split()
            looks_like_name = (2 <= len(candidate_words) <= 4
                                 and all(w.replace("'", "").isalpha() for w in candidate_words)
                                 and not any(h in candidate.upper() for h in all_hints))
            if looks_like_name:
                fields["name"] = ExtractedField(candidate.upper(), "UNCERTAIN", "LOW",
                                                  f"positional: line before DOB ({dob_field.source!r})")

    for key in _ALL_FIELD_KEYS:
        fields.setdefault(key, ExtractedField("", "NOT_DETECTED", "-", ""))
    return fields
