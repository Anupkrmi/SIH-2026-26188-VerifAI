"""Evidence fusion: the Trust Ladder's decision rule, and the reason this
system is safe to deploy despite the field's published error rates (see
docs/01-RESEARCH.md -- the best industrial document-forgery detector
scores 26.52% EER on unseen documents).

This is NOT a single additive score banded into a verdict. Tier is
decisive, not just heavily weighted -- exactly the Trust Ladder principle
in docs/03-ARCHITECTURE.md:

  T0 crypto      -- decisive BOTH ways. Invalid signature forces CRITICAL
                    regardless of everything else; valid signature plus a
                    clean T1 is the strongest clearance this system gives.
  T1 rules       -- decisive AGAINST only. Any failure here (an MRZ
                    checksum, a cross-zone mismatch, an expiry violation)
                    forces CRITICAL on its own. A forger who gets the
                    pixels right but breaks a rule does not get partial
                    credit for the pixels.
  T2 forensics / -- ADVISORY ONLY. These signals still count -- they set
     biometric      the band among LOW/MEDIUM/HIGH -- but they can never
                    push a document past HIGH by themselves. A model can
                    raise a document for a human to look at; it can never
                    condemn one alone.

An earlier version of this module scored everything as one additive total
and banded it (the illustrative weights sketch in the plan). That fails
its own acceptance test: a single cross-zone mismatch (weight 25) lands
inside the LOW band (0-25) under plain addition, which is the opposite of
"decisive against". Tier-first branching, not a weight tuned to dodge a
boundary, is the actual fix.

The recommended-action text is never an accusation, at any band -- see
policy.yaml and the language rule in docs/02-STRATEGY.md.
"""
from __future__ import annotations

from core.rules.engine import load_policy
from core.types import Band, Severity, Signal, Tier, Verdict

_DECISIVE_TIERS = {Tier.RULES}  # crypto handled separately via crypto_valid; forensics/biometric are advisory-only by omission from this set


def _band_for_score(score: int, policy: dict) -> tuple[Band, str]:
    for lo, hi, name, action in policy["risk_bands"]:
        if lo <= score <= hi:
            return Band(name), action
    return Band.HIGH, "Secondary inspection recommended"


def fuse(signals: list[Signal], crypto_valid: bool | None = None, policy: dict | None = None
          ) -> Verdict:
    """crypto_valid: None if no cryptographic tier was evaluated at all
    (e.g. no chip/signed manifest presented); True/False if it was."""
    policy = policy or load_policy()
    fails = [s for s in signals if s.severity == Severity.FAIL]
    raw_score = max(0, min(100, sum(s.weight for s in fails)))

    if crypto_valid is False:
        return Verdict(score=100, band=Band.CRITICAL,
                        action="Secondary inspection recommended",
                        signals=signals, crypto_override=True)

    decisive_failed = any(s.tier in _DECISIVE_TIERS for s in fails)
    if decisive_failed:
        return Verdict(score=max(raw_score, 76), band=Band.CRITICAL,
                        action="Secondary inspection recommended",
                        signals=signals, crypto_override=False)

    # Nothing decisive failed (crypto_valid is True or None): only
    # advisory (forensics/biometric) evidence remains, if any. Band it
    # normally, but it is structurally incapable of reaching CRITICAL --
    # that band is reserved for a decisive failure, never for a model's
    # opinion.
    #
    # An earlier version of this branch let crypto_valid is True shortcut
    # straight to LOW here, before ever looking at raw_score. That was a
    # real bug, not just an early return: it meant a document with a
    # verified-untampered signature but a genuinely fired forensic signal
    # (e.g. a screen recapture, self-signed at intake -- crypto correctly
    # PASSES because nothing has changed since signing, but recapture.py
    # still fired) got reported as a clean LOW/GREEN, silently erasing the
    # forensic finding. Found by running the full pipeline against every
    # attack once crypto was actually wired in, not by inspecting this
    # function in isolation. Crypto proving "unaltered since signing" and
    # forensics finding "something looks suspicious in what was captured"
    # are answers to two different questions; one must never suppress the
    # other.
    band, action = _band_for_score(raw_score, policy)
    if band == Band.CRITICAL:
        band, action = Band.HIGH, "Secondary inspection recommended"

    if crypto_valid is True and raw_score == 0:
        # cryptographic proof AND a genuinely clean advisory record: the
        # strongest clearance this system gives.
        band, action = Band.LOW, "No action required"

    return Verdict(score=raw_score, band=band, action=action, signals=signals,
                    crypto_override=False)


_TRAFFIC_LIGHT = {Band.LOW: "GREEN", Band.MEDIUM: "AMBER", Band.HIGH: "AMBER", Band.CRITICAL: "RED"}


def traffic_light(band: Band) -> str:
    return _TRAFFIC_LIGHT[band]
