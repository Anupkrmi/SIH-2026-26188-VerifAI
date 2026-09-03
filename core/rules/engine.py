"""Deterministic policy rules over the MRZ-decoded fields (the Trust
Ladder's T1 tier: forgeable, but self-checking, and decisive against a
document when violated -- never decisive in a document's favour on its
own). Five concrete, named checks rather than a general rule-expression
language: policy.yaml carries every weight and threshold these checks use,
so MHA/SSB staff can retune them without touching Python, but the checks
themselves are plain functions -- a generic YAML expression interpreter
would be real engineering effort this sprint has no use for.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import yaml

from config import PATHS
from core.mrz import MrzFields
from core.types import Severity, Signal, Tier

_policy_cache: dict | None = None


def load_policy(path: Path | None = None) -> dict:
    global _policy_cache
    if _policy_cache is None or path is not None:
        with open(path or PATHS["policy"], encoding="utf-8") as f:
            _policy_cache = yaml.safe_load(f)
    return _policy_cache


def _weight(policy: dict, weight_key: str) -> int:
    return int(policy["risk_weights"][weight_key])


def _rule_expiry_in_past(fields: MrzFields, today: dt.date, cfg: dict, policy: dict) -> Signal:
    ok = fields.date_of_expiry >= today
    msg = "Document is within its validity period" if ok else cfg["message"].format(expiry=fields.date_of_expiry)
    return Signal(tier=Tier.RULES, check="expiry_in_past",
                  severity=Severity.PASS if ok else Severity.FAIL,
                  weight=0 if ok else _weight(policy, cfg["weight_key"]), message=msg)


def _rule_issue_after_expiry(fields: MrzFields, today: dt.date, cfg: dict, policy: dict) -> Signal:
    issue = getattr(fields, "date_of_issue", None)
    if issue is None:
        return Signal(tier=Tier.RULES, check="issue_after_expiry", severity=Severity.PASS,
                       weight=0, message="No issue date available to check")
    ok = issue <= fields.date_of_expiry
    msg = "Issue date precedes expiry date" if ok else cfg["message"].format(issue=issue, expiry=fields.date_of_expiry)
    return Signal(tier=Tier.RULES, check="issue_after_expiry",
                  severity=Severity.PASS if ok else Severity.FAIL,
                  weight=0 if ok else _weight(policy, cfg["weight_key"]), message=msg)


def _rule_dob_in_future(fields: MrzFields, today: dt.date, cfg: dict, policy: dict) -> Signal:
    ok = fields.date_of_birth <= today
    msg = "Date of birth is not in the future" if ok else cfg["message"].format(dob=fields.date_of_birth)
    return Signal(tier=Tier.RULES, check="dob_in_future",
                  severity=Severity.PASS if ok else Severity.FAIL,
                  weight=0 if ok else _weight(policy, cfg["weight_key"]), message=msg)


def _rule_dob_implies_age_over_max(fields: MrzFields, today: dt.date, cfg: dict, policy: dict) -> Signal:
    max_years = cfg.get("max_age_years", 120)
    age_years = (today - fields.date_of_birth).days / 365.25
    ok = age_years <= max_years
    msg = ("Implied age is within plausible range" if ok
           else cfg["message"].format(dob=fields.date_of_birth, max_age_years=max_years))
    return Signal(tier=Tier.RULES, check="dob_implies_age_over_max",
                  severity=Severity.PASS if ok else Severity.FAIL,
                  weight=0 if ok else _weight(policy, cfg["weight_key"]), message=msg)


def _rule_document_number_format(fields: MrzFields, today: dt.date, cfg: dict, policy: dict) -> Signal:
    ok = re.match(cfg["pattern"], fields.passport_number) is not None
    msg = ("Passport number matches the expected issuer format" if ok
           else cfg["message"].format(passport_number=fields.passport_number))
    return Signal(tier=Tier.RULES, check="document_number_format",
                  severity=Severity.PASS if ok else Severity.FAIL,
                  weight=0 if ok else _weight(policy, cfg["weight_key"]), message=msg)


def _rule_six_month_validity(fields: MrzFields, today: dt.date, cfg: dict, policy: dict) -> Signal:
    min_months = cfg.get("min_months_remaining", 6)
    remaining_days = (fields.date_of_expiry - today).days
    ok = remaining_days >= min_months * 30
    msg = ("Sufficient remaining validity" if ok
           else cfg["message"].format(min_months_remaining=min_months))
    return Signal(tier=Tier.RULES, check="six_month_validity",
                  severity=Severity.PASS if ok else Severity.FAIL,
                  weight=0 if ok else _weight(policy, cfg["weight_key"]), message=msg)


_RULE_FUNCTIONS = {
    "expiry_in_past": _rule_expiry_in_past,
    "issue_after_expiry": _rule_issue_after_expiry,
    "dob_in_future": _rule_dob_in_future,
    "dob_implies_age_over_max": _rule_dob_implies_age_over_max,
    "document_number_format": _rule_document_number_format,
    "six_month_validity": _rule_six_month_validity,
}


def evaluate(fields: MrzFields, today: dt.date | None = None, policy: dict | None = None
             ) -> list[Signal]:
    """Run every enabled rule from policy.yaml against MRZ-decoded fields --
    the authoritative source per the Trust Ladder, since the MRZ is
    self-checking (see core/mrz.py) while the VIZ is not."""
    policy = policy or load_policy()
    today = today or dt.date.today()
    signals = []
    for rule_name, cfg in policy["rules"].items():
        if not cfg.get("enabled", False):
            continue
        fn = _RULE_FUNCTIONS[rule_name]
        signals.append(fn(fields, today, cfg, policy))
    return signals


if __name__ == "__main__":
    import datetime as _dt
    demo = MrzFields(
        issuing_state="UTO", surname="TEST", given_names="DEMO",
        passport_number="123456789", nationality="UTO",
        date_of_birth=_dt.date(1990, 1, 1), sex="M",
        date_of_expiry=_dt.date(2030, 1, 1),
    )
    for s in evaluate(demo):
        print(f"  {s.check:28s} {s.severity.value:5s} weight={s.weight:3d}  {s.message}")
