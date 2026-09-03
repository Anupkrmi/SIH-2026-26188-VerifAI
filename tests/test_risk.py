"""core/risk.py acceptance tests: the three Trust Ladder invariants that
are the entire reason this module exists, not the additive arithmetic.
"""
from core.risk import fuse, traffic_light
from core.types import Band, Severity, Signal, Tier


def _sig(tier, check, severity, weight=0, message="") -> Signal:
    return Signal(tier=tier, check=check, severity=severity, weight=weight, message=message)


def test_all_pass_with_no_crypto_tier_is_low():
    signals = [_sig(Tier.RULES, "expiry_in_past", Severity.PASS)]
    v = fuse(signals, crypto_valid=None)
    assert v.band == Band.LOW
    assert traffic_light(v.band) == "GREEN"


def test_invalid_signature_forces_critical_regardless_of_everything_else():
    """T0 is decisive both ways: even with zero rule failures, an invalid
    signature must force CRITICAL. This is the one-pixel-changes-the-
    portrait demo's whole point."""
    signals = [_sig(Tier.RULES, "expiry_in_past", Severity.PASS)]
    v = fuse(signals, crypto_valid=False)
    assert v.band == Band.CRITICAL
    assert traffic_light(v.band) == "RED"
    assert v.crypto_override is True


def test_valid_signature_and_clean_rules_is_the_strongest_clearance():
    signals = [_sig(Tier.RULES, "expiry_in_past", Severity.PASS)]
    v = fuse(signals, crypto_valid=True)
    assert v.band == Band.LOW


def test_any_rules_failure_is_decisive_against_alone():
    """T1 is decisive against: a single cross-zone mismatch must fail the
    document outright, not merely add points to a score that might still
    land in a clean band. This is the property the naive additive-weight
    sketch in the plan failed (25 points landed inside the 0-25 LOW band)."""
    signals = [_sig(Tier.RULES, "crosszone_date_of_birth", Severity.FAIL, weight=25)]
    v = fuse(signals, crypto_valid=None)
    assert v.band == Band.CRITICAL
    assert traffic_light(v.band) == "RED"


def test_rules_failure_beats_even_a_valid_signature():
    """Cryptography proves the CHIP's data is authentic and unmodified; it
    does not prove the VIZ agrees with it. A rules failure must still win."""
    signals = [_sig(Tier.RULES, "crosszone_date_of_birth", Severity.FAIL, weight=25)]
    v = fuse(signals, crypto_valid=True)
    assert v.band == Band.CRITICAL


def test_forensics_alone_cannot_reach_critical():
    """T2 is advisory only: a model can raise a document for review, but
    cannot condemn one by itself, however high its own confidence."""
    signals = [_sig(Tier.FORENSICS, "recapture_detected", Severity.FAIL, weight=90)]
    v = fuse(signals, crypto_valid=None)
    assert v.band != Band.CRITICAL
    assert v.band == Band.HIGH
    assert traffic_light(v.band) == "AMBER"


def test_biometric_alone_cannot_reach_critical():
    signals = [_sig(Tier.BIOMETRIC, "face_mismatch", Severity.FAIL, weight=90)]
    v = fuse(signals, crypto_valid=None)
    assert v.band != Band.CRITICAL


def test_recommended_action_is_never_an_accusation():
    accusatory_words = ["fraud", "criminal", "fake", "liar", "guilty"]
    cases = [
        fuse([_sig(Tier.RULES, "x", Severity.FAIL, weight=100)], crypto_valid=None),
        fuse([_sig(Tier.FORENSICS, "x", Severity.FAIL, weight=100)], crypto_valid=None),
        fuse([], crypto_valid=False),
    ]
    for v in cases:
        lowered = v.action.lower()
        assert not any(w in lowered for w in accusatory_words), v.action
