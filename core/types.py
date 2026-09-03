"""Shared contracts between pipeline stages.

Every stage (mrz, crosszone, rules, forensics, face, crypto) emits a list of
Signal. risk.py fuses Signals into a Verdict. pipeline.py assembles a Case.
Nothing downstream ever inspects a stage's internals directly -- only Signal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Tier(str, Enum):
    """The Trust Ladder. Order matters: see core/risk.py for the override
    rules that keep a lower tier from ever outranking a higher one."""
    CRYPTO = "crypto"           # T0 -- decisive both ways
    RULES = "rules"             # T1 -- decisive against, never a clearance
    FORENSICS = "forensics"     # T2 -- advisory only
    BIOMETRIC = "biometric"     # T2 -- advisory only


class Severity(str, Enum):
    PASS = "pass"
    WEAK = "weak"       # signal present but explicitly untrusted (e.g. ELA)
    FAIL = "fail"


class Signal(BaseModel):
    """One atomic check result."""
    tier: Tier
    check: str                      # e.g. "mrz_checksum", "photo_region"
    severity: Severity
    weight: int = 0                 # points added to the risk score if FAIL
    message: str                    # human-readable, never accusatory
    detail: dict = Field(default_factory=dict)  # values compared, bbox, etc.


class Band(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Verdict(BaseModel):
    score: int
    band: Band
    action: str                     # never an accusation -- see core/risk.py
    signals: list[Signal]
    crypto_override: bool = False   # True if T0 forced the band


class Case(BaseModel):
    case_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_image: str                # path, relative to data/
    attack_label: Optional[str] = None   # ground truth, if this is a synth attack
    verdict: Optional[Verdict] = None
    notes: str = ""
