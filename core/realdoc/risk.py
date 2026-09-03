"""Dynamic Trust Ladder + additive risk fusion for real-document mode.

Deliberately separate from core/risk.py's fuse(), which is decisive-tier
based and assumes Mode A's guarantees (a known template, a resolvable
signed manifest). A real upload has neither by default, so this module:

  - never reaches CRITICAL. That band is reserved for a decisive
    cryptographic proof of tampering (see core/risk.py's own docstring) --
    a real document with no signed manifest structurally cannot produce
    that proof, so claiming CRITICAL here would be exactly the false
    certainty the project's language rule forbids.
  - can return the band "REVIEW" instead of a score-derived one, when the
    pipeline could not gather enough evidence to say anything at all.
    "Could not determine" and "determined to be fine" are different claims;
    collapsing both into LOW would hide the system's own uncertainty.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.rules.engine import load_policy
from core.types import Severity, Signal

VALID_STATUSES = {"VERIFIED", "REVIEW", "FAILED", "NOT_APPLICABLE"}


@dataclass
class LadderStep:
    name: str
    status: str          # one of VALID_STATUSES
    detail: str = ""


@dataclass
class RealDocVerdict:
    score: int
    band: str             # "LOW" | "MEDIUM" | "HIGH" | "REVIEW"
    action: str
    steps: list[LadderStep] = field(default_factory=list)
    signals: list[Signal] = field(default_factory=list)


def fuse_realdoc(signals: list[Signal], steps: list[LadderStep],
                   insufficient_evidence: bool, policy: dict | None = None) -> RealDocVerdict:
    policy = policy or load_policy()
    fails = [s for s in signals if s.severity == Severity.FAIL]
    score = max(0, min(100, sum(s.weight for s in fails)))

    if insufficient_evidence:
        return RealDocVerdict(score=score, band="REVIEW",
                               action="Insufficient evidence — secondary inspection recommended",
                               steps=steps, signals=signals)

    band, action = "LOW", "No action required"
    for lo, hi, name, act in policy["risk_bands"]:
        if lo <= score <= hi:
            band, action = name, act
            break
    if band == "CRITICAL":   # real-doc mode has no decisive crypto proof available -- cap at HIGH
        band, action = "HIGH", "Secondary inspection recommended"

    return RealDocVerdict(score=score, band=band, action=action, steps=steps, signals=signals)
