"""Generic validation for the fields core/realdoc/fields.py extracts --
NOT the ICAO/UTO-specific rules in core/rules/ (Mode A only, untouched).
Returns core.types.Signal so core/realdoc/risk.py can fuse these exactly
like any other tier-1 evidence, reusing the same policy.yaml risk_weights
rather than inventing a second set of numbers.
"""
from __future__ import annotations

import datetime as _dt

from core.realdoc.fields import ExtractedField
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier


def _parsed(fields: dict[str, ExtractedField], key: str) -> _dt.date | None:
    f = fields.get(key)
    if not f or f.status == "NOT_DETECTED" or not f.value:
        return None
    try:
        return _dt.date.fromisoformat(f.value)
    except ValueError:
        return None


def validate_fields(fields: dict[str, ExtractedField], policy: dict | None = None) -> list[Signal]:
    policy = policy or load_policy()
    mismatch_weight = int(policy["risk_weights"]["cross_field_mismatch"])
    expired_weight = int(policy["risk_weights"]["expired_document"])
    today = _dt.date.today()
    signals: list[Signal] = []

    dob = _parsed(fields, "date_of_birth")
    if dob is not None:
        if dob > today:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_dob_future", severity=Severity.FAIL,
                                    weight=mismatch_weight, message=f"Date of birth ({dob}) is in the future"))
        elif (today.year - dob.year) > 120:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_dob_age", severity=Severity.FAIL,
                                    weight=mismatch_weight,
                                    message=f"Date of birth ({dob}) implies an age over 120 years"))
        else:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_dob_future", severity=Severity.PASS,
                                    weight=0, message=f"Date of birth ({dob}) is a plausible date"))

    expiry = _parsed(fields, "date_of_expiry")
    if expiry is not None:
        if expiry < today:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_expired", severity=Severity.FAIL,
                                    weight=expired_weight,
                                    message=f"Document expiry date ({expiry}) is in the past"))
        else:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_expired", severity=Severity.PASS,
                                    weight=0, message=f"Document expiry date ({expiry}) has not passed"))

    issue = _parsed(fields, "date_of_issue")
    if issue is not None and expiry is not None:
        if issue > expiry:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_issue_after_expiry", severity=Severity.FAIL,
                                    weight=mismatch_weight,
                                    message=f"Date of issue ({issue}) is after date of expiry ({expiry})"))
        else:
            signals.append(Signal(tier=Tier.RULES, check="realdoc_issue_after_expiry", severity=Severity.PASS,
                                    weight=0, message="Issue and expiry dates are consistent"))

    return signals
