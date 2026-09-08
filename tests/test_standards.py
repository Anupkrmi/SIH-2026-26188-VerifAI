"""core/knowledge/standards.py acceptance tests: every check name that
can actually appear as a FAIL in a real verdict must resolve to a sourced
explanation (or the UI silently shows nothing, which is a worse failure
mode than an assertion here), and nothing in STANDARDS may look like an
invented citation.
"""
from core.knowledge.standards import STANDARDS, lookup


def test_exact_key_matches_itself():
    assert lookup("mrz_checksum") is STANDARDS["mrz_checksum"]


def test_longest_prefix_wins():
    """mrz_checksum_date_of_birth must resolve via "mrz_checksum", not
    fail to match or match some shorter, wrong key."""
    assert lookup("mrz_checksum_date_of_birth") == STANDARDS["mrz_checksum"]
    assert lookup("issuer_status_revoked") == STANDARDS["issuer_status"]
    assert lookup("issuer_status_stolen") == STANDARDS["issuer_status"]
    assert lookup("issuer_status_expired") == STANDARDS["issuer_status"]
    assert lookup("issuer_status_invalid") == STANDARDS["issuer_status"]


def test_unknown_check_returns_none_rather_than_a_guess():
    assert lookup("some_check_nobody_wrote_yet") is None


def test_every_real_fail_check_this_build_can_produce_is_sourced():
    """The actual check names core/rules/engine.py, core/forensics/*.py,
    core/crypto/manifest.py, core/face/pipeline.py and core/issuer/*.py
    can emit as a FAIL -- every one must resolve to an explanation, so
    "Why is this required?" never silently renders nothing for a real
    finding."""
    real_fail_checks = [
        "mrz_checksum_passport_number", "mrz_checksum_date_of_birth",
        "crosszone_date_of_birth", "crosszone_surname",
        "expiry_in_past", "issue_after_expiry", "dob_in_future",
        "dob_implies_age_over_max", "document_number_format",
        "manifest_match", "signature_valid", "signature_chain",
        "photo_region_anomaly", "noise_residual_anomaly", "recapture_anomaly",
        "face_verification",
        "issuer_status_revoked", "issuer_status_stolen", "issuer_status_expired",
        "issuer_status_invalid", "issuer_field_mismatch", "issuer_lookup",
        "identity_linkage",
    ]
    unsourced = [c for c in real_fail_checks if lookup(c) is None]
    assert unsourced == [], f"no sourced explanation for: {unsourced}"


def test_no_entry_claims_a_fake_precise_citation():
    """Guards the module's own stated discipline: an ICAO source may name
    a Part, never a fabricated clause/section number this build never
    verified against the primary document."""
    for key, entry in STANDARDS.items():
        source = entry["source"]
        if "ICAO" in source:
            assert "Part" in source, f"{key}: ICAO source without a Part-level citation: {source!r}"
            assert "Section" not in source, \
                f"{key}: claims section-level precision that wasn't verified: {source!r}"
        assert entry["rule"], f"{key}: empty rule text"
        assert entry["note"], f"{key}: empty note (should point at the implementing file)"
