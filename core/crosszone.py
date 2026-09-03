"""VIZ vs MRZ consistency: the highest-yield deterministic forgery check
there is, per the commercial-vendor literature cited in docs/01-RESEARCH.md
-- a forger edits the printed field a human reads and forgets the field a
machine reads, or vice versa. Both zones are read from pixels (core.mrz,
core.viz_ocr), never from generation-time metadata: this must work on a
document the pipeline has never seen the ground truth for.
"""
from __future__ import annotations

import numpy as np

from core.mrz import decode_fields, read_td3
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier
from core.viz_ocr import read_field

# VIZ field key -> MRZ-decoded MrzFields attribute it should agree with.
# date_of_issue has no MRZ counterpart at all (ICAO Doc 9303 does not
# encode it) and is deliberately absent from this table.
_COMPARABLE = {
    "surname": "surname",
    "given_names": "given_names",
    "passport_number": "passport_number",
    "nationality": "nationality",
    "sex": "sex",
}


def _normalise(s: str) -> str:
    return s.strip().upper()


def compare(gray: np.ndarray, mrz_band_bbox: tuple[int, int, int, int], policy: dict | None = None
            ) -> list[Signal]:
    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["cross_field_mismatch"])
    signals: list[Signal] = []

    line1, line2, _ = read_td3(gray, mrz_band_bbox)
    mrz_fields = decode_fields(line1, line2)

    for viz_key, mrz_attr in _COMPARABLE.items():
        viz_value, _ = read_field(gray, viz_key)
        mrz_value = str(getattr(mrz_fields, mrz_attr))
        ok = _normalise(viz_value) == _normalise(mrz_value)
        signals.append(Signal(
            tier=Tier.RULES,
            check=f"crosszone_{viz_key}",
            severity=Severity.PASS if ok else Severity.FAIL,
            weight=0 if ok else weight,
            message=(f"{viz_key.replace('_', ' ')} matches between the printed field and the MRZ"
                      if ok else
                      f"{viz_key.replace('_', ' ')} mismatch: printed field reads "
                      f"{viz_value!r}, MRZ reads {mrz_value!r}"),
            detail={"viz": viz_value, "mrz": mrz_value},
        ))

    # date_of_birth and date_of_expiry are read from the VIZ as formatted
    # strings ("24 JAN 1977"); compare the underlying dates, not strings,
    # so a display-format difference is never mistaken for a real mismatch.
    import datetime as dt
    for date_key, mrz_attr in [("date_of_birth", "date_of_birth"), ("date_of_expiry", "date_of_expiry")]:
        viz_text, _ = read_field(gray, date_key)
        mrz_date = getattr(mrz_fields, mrz_attr)
        try:
            viz_date = dt.datetime.strptime(viz_text, "%d %b %Y").date()
            parse_ok = True
        except ValueError:
            viz_date, parse_ok = None, False
        ok = parse_ok and viz_date == mrz_date
        signals.append(Signal(
            tier=Tier.RULES,
            check=f"crosszone_{date_key}",
            severity=Severity.PASS if ok else Severity.FAIL,
            weight=0 if ok else weight,
            message=(f"{date_key.replace('_', ' ')} matches between the printed field and the MRZ"
                      if ok else
                      f"{date_key.replace('_', ' ')} mismatch: printed field reads "
                      f"{viz_text!r} ({viz_date}), MRZ reads {mrz_date}"),
            detail={"viz": viz_text, "viz_parsed": str(viz_date), "mrz": str(mrz_date)},
        ))

    return signals
