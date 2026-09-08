"""core/issuer/*.py acceptance tests: registry lookup/status handling,
field comparison, integrity (fingerprint + signed manifest), and the
Tier.ISSUER risk-fusion invariant. Every test except the pipeline-
integration one at the bottom uses a throwaway tmp_path registry, never
the committed data/registry/registry.db.
"""
from __future__ import annotations

import datetime as dt
import sqlite3

import pytest

from config import PATHS
from core.issuer.compare import compare_to_document
from core.issuer.integrity import record_fingerprint
from core.issuer.models import RegistryRecord, RegistryStatus
from core.issuer.registry import SyntheticIssuerRegistry, get_default_registry, init_db, insert_record
from core.mrz import MrzFields
from core.risk import fuse
from core.rules.engine import load_policy
from core.types import Band, Severity, Signal, Tier

_CREATED = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _record(**overrides) -> RegistryRecord:
    base = dict(
        registry_record_id="REG-T1", document_number="123456789", document_type="PASSPORT",
        issuer_id="UTO-DEMO-AUTH", person_id="P900", name="DOE JANE",
        date_of_birth=dt.date(1990, 1, 1), nationality="UTO",
        issue_date=dt.date(2020, 1, 1), expiry_date=dt.date(2030, 1, 1),
        status=RegistryStatus.ACTIVE, created_at=_CREATED,
    )
    base.update(overrides)
    record = RegistryRecord(**base)
    record.issuer_signature = record_fingerprint(record)
    return record


def _fields(**overrides) -> MrzFields:
    base = dict(
        issuing_state="UTO", surname="DOE", given_names="JANE", passport_number="123456789",
        nationality="UTO", date_of_birth=dt.date(1990, 1, 1), sex="F",
        date_of_expiry=dt.date(2030, 1, 1),
    )
    base.update(overrides)
    return MrzFields(**base)


@pytest.fixture
def registry(tmp_path) -> SyntheticIssuerRegistry:
    db_path = tmp_path / "registry.db"
    init_db(db_path)
    return SyntheticIssuerRegistry(db_path, tmp_path / "manifest.json")


# ------------------------------------------------------------------- lookup ---

def test_lookup_returns_none_for_an_unknown_document_number(registry):
    assert registry.lookup("000000000") is None


def test_lookup_finds_an_inserted_record(registry):
    insert_record(registry.db_path, _record())
    found = registry.lookup("123456789")
    assert found is not None
    assert found.status == RegistryStatus.ACTIVE
    assert found.name == "DOE JANE"


def test_stats_counts_by_status(registry):
    insert_record(registry.db_path, _record(registry_record_id="A", document_number="1"))
    insert_record(registry.db_path, _record(registry_record_id="B", document_number="2",
                                               status=RegistryStatus.REVOKED))
    insert_record(registry.db_path, _record(registry_record_id="C", document_number="3",
                                               status=RegistryStatus.REVOKED))
    stats = registry.stats()
    assert stats["ACTIVE"] == 1
    assert stats["REVOKED"] == 2
    assert stats["TOTAL"] == 3


# ------------------------------------------------------- compare_to_document ---

def test_not_found_never_reads_as_fake():
    """A document number the registry has never heard of is NOT evidence of
    forgery -- it's evidence the registry can't help. WEAK severity costs
    zero risk points on its own."""
    policy = load_policy()
    signal = compare_to_document(_fields(), None, policy)
    assert signal.severity == Severity.WEAK
    assert signal.weight == 0
    assert "could not be established" in signal.message
    for word in ("fake", "forged", "fraud"):
        assert word not in signal.message.lower()


def test_active_matching_record_passes_clean():
    policy = load_policy()
    signal = compare_to_document(_fields(), _record(), policy)
    assert signal.severity == Severity.PASS
    assert signal.weight == 0
    assert signal.tier == Tier.ISSUER


def test_revoked_status_fails_decisively():
    policy = load_policy()
    record = _record(status=RegistryStatus.REVOKED, revocation_reason="Reported lost")
    signal = compare_to_document(_fields(), record, policy)
    assert signal.severity == Severity.FAIL
    assert signal.weight > 0
    assert "REVOKED" in signal.message
    assert "Reported lost" in signal.message


def test_stolen_status_fails_decisively():
    policy = load_policy()
    signal = compare_to_document(_fields(), _record(status=RegistryStatus.STOLEN), policy)
    assert signal.severity == Severity.FAIL
    assert "STOLEN" in signal.message


def test_expired_status_fails_with_the_expiry_weight():
    policy = load_policy()
    signal = compare_to_document(_fields(), _record(status=RegistryStatus.EXPIRED), policy)
    assert signal.severity == Severity.FAIL
    assert signal.weight == policy["risk_weights"]["expired_document"]


def test_field_mismatch_is_detected_and_named():
    """The actual question this feature exists to answer: a valid document
    NUMBER whose name/DOB disagree with the registry must be caught and
    explained, not silently passed because the number matched."""
    policy = load_policy()
    presented = _fields(surname="SMITH", given_names="JOHN", date_of_birth=dt.date(1985, 6, 15))
    signal = compare_to_document(presented, _record(), policy)
    assert signal.severity == Severity.FAIL
    assert signal.check == "issuer_field_mismatch"
    assert signal.detail["fields"]["name"] is False
    assert signal.detail["fields"]["date_of_birth"] is False
    assert signal.detail["fields"]["document_number"] is True
    assert "name" in signal.message and "date_of_birth" in signal.message


# ------------------------------------------------------------------- linkage ---

def test_find_linked_records_is_empty_for_a_unique_cluster(registry):
    insert_record(registry.db_path, _record(portrait_reference="PORTRAIT-CLUSTER-A"))
    assert registry.find_linked_records("PORTRAIT-CLUSTER-A", exclude_record_id="REG-T1") == []


def test_find_linked_records_finds_a_shared_cluster_excluding_self(registry):
    insert_record(registry.db_path, _record(registry_record_id="A", document_number="1",
                                               portrait_reference="PORTRAIT-CLUSTER-X"))
    insert_record(registry.db_path, _record(registry_record_id="B", document_number="2",
                                               portrait_reference="PORTRAIT-CLUSTER-X"))
    linked = registry.find_linked_records("PORTRAIT-CLUSTER-X", exclude_record_id="A")
    assert [r.registry_record_id for r in linked] == ["B"]


def test_find_linked_records_handles_no_portrait_reference(registry):
    assert registry.find_linked_records(None, exclude_record_id="REG-T1") == []
    assert registry.find_linked_records("", exclude_record_id="REG-T1") == []


def test_check_identity_linkage_is_none_when_no_record_found():
    from core.issuer.linkage import check_identity_linkage
    policy = load_policy()
    assert check_identity_linkage(None, get_default_registry(), policy) is None


def test_check_identity_linkage_passes_clean_for_a_unique_cluster(registry):
    from core.issuer.linkage import check_identity_linkage
    record = _record(portrait_reference="PORTRAIT-CLUSTER-UNIQUE")
    insert_record(registry.db_path, record)
    signal = check_identity_linkage(record, registry, load_policy())
    assert signal.severity == Severity.PASS
    assert signal.weight == 0
    assert signal.tier == Tier.IDENTITY


def test_check_identity_linkage_fails_advisory_for_a_shared_cluster(registry):
    from core.issuer.linkage import check_identity_linkage
    a = _record(registry_record_id="A", document_number="1", name="ONE PERSON",
                 portrait_reference="PORTRAIT-CLUSTER-SHARED")
    b = _record(registry_record_id="B", document_number="2", name="TWO PERSON",
                 portrait_reference="PORTRAIT-CLUSTER-SHARED")
    insert_record(registry.db_path, a)
    insert_record(registry.db_path, b)
    signal = check_identity_linkage(a, registry, load_policy())
    assert signal.severity == Severity.FAIL
    assert signal.weight > 0
    assert signal.tier == Tier.IDENTITY
    assert "possible" in signal.message.lower()
    assert signal.detail["linked"][0]["registry_record_id"] == "B"


def test_identity_tier_is_not_decisive():
    """The whole reason this feature is safe to ship: a linkage FAIL must
    never, on its own, force CRITICAL -- only RULES and ISSUER do."""
    from core.risk import fuse
    signal = Signal(tier=Tier.IDENTITY, check="identity_linkage", severity=Severity.FAIL,
                      weight=90, message="Possible identity linkage detected: also associated with X")
    v = fuse([signal], crypto_valid=None)
    assert v.band != Band.CRITICAL
    assert v.band == Band.HIGH


# ------------------------------------------------------------------ integrity ---

def test_registry_with_no_records_is_trivially_valid(registry):
    ok, detail = registry.verify_integrity()
    assert ok
    assert detail["record_count"] == 0


def test_registry_is_valid_after_signing(registry):
    insert_record(registry.db_path, _record())
    ok, detail = registry.verify_integrity()
    assert ok, detail


def test_hand_edited_status_is_detected_without_recomputing_the_fingerprint(registry):
    """The REVOKED -> ACTIVE demo attack: flip a stored status in place,
    leaving the old fingerprint untouched. Must be caught from the
    fingerprint mismatch alone, before the manifest signature is even
    checked."""
    record = _record(status=RegistryStatus.REVOKED)
    insert_record(registry.db_path, record)
    assert registry.verify_integrity()[0] is True

    conn = sqlite3.connect(registry.db_path)
    conn.execute("UPDATE records SET status = 'ACTIVE' WHERE registry_record_id = ?",
                  (record.registry_record_id,))
    conn.commit()
    conn.close()

    ok, detail = registry.verify_integrity()
    assert ok is False
    assert record.registry_record_id in detail["tampered_record_ids"]


def test_tampering_survives_a_fresh_process_restart(registry):
    """Not just an in-memory check: a NEW SyntheticIssuerRegistry instance
    (as if the app restarted) must still catch the same tamper from disk
    alone -- detection can't depend on process state."""
    record = _record()
    insert_record(registry.db_path, record)
    registry.verify_integrity()  # signs the manifest once

    conn = sqlite3.connect(registry.db_path)
    conn.execute("UPDATE records SET name = 'MALLORY ATTACKER' WHERE registry_record_id = ?",
                  (record.registry_record_id,))
    conn.commit()
    conn.close()

    fresh = SyntheticIssuerRegistry(registry.db_path, registry.manifest_path)
    ok, detail = fresh.verify_integrity()
    assert ok is False
    assert record.registry_record_id in detail["tampered_record_ids"]


# --------------------------------------------------------------- risk fusion ---

def _sig(tier, check, severity, weight=0, message="") -> Signal:
    return Signal(tier=tier, check=check, severity=severity, weight=weight, message=message)


def test_issuer_revoked_forces_critical_alone():
    """Tier.ISSUER is decisive-against, the same authority class as
    Tier.RULES (core/risk.py's _DECISIVE_TIERS) -- a REVOKED registry hit
    must force CRITICAL on its own, nothing else wrong on the document."""
    signals = [_sig(Tier.ISSUER, "issuer_status_revoked", Severity.FAIL, weight=30,
                      message="Registry record for this document is REVOKED (x)")]
    v = fuse(signals, crypto_valid=None)
    assert v.band == Band.CRITICAL


def test_issuer_not_found_alone_does_not_raise_the_band():
    signals = [_sig(Tier.ISSUER, "issuer_lookup", Severity.WEAK, weight=0,
                      message="Issuance could not be established from the configured registry.")]
    v = fuse(signals, crypto_valid=None)
    assert v.band == Band.LOW


# --------------------------------------------------------- pipeline integration ---

GENUINE = PATHS["documents"] / "demo_0001.png"

pytestmark = pytest.mark.skipif(
    not (GENUINE.exists() and PATHS["registry_db"].exists()),
    reason="run `python -m synth.passport && python -m synth.registry` first",
)


def test_seed_registry_has_a_shared_portrait_cluster_for_multiple_identity_detection():
    """Data-level acceptance test for the seed data itself, not the
    (not-yet-built) detection algorithm: the committed registry must
    contain at least one portrait_reference shared by two records with
    different person_id -- Feature 4's precondition. synth/registry.py
    seeds REG-0006/REG-0007 for exactly this."""
    from core.issuer.registry import get_default_registry
    records = get_default_registry().all_records()
    clusters: dict[str, set[str]] = {}
    for r in records:
        clusters.setdefault(r.portrait_reference, set()).add(r.person_id)
    linked = {ref: people for ref, people in clusters.items() if len(people) > 1}
    assert linked, "expected at least one portrait_reference shared across distinct person_ids"


def test_seed_registry_has_every_status_and_every_column_populated():
    """'Fully populated' as a checkable fact, not a claim: every status
    value has at least one row, and no row has a blank document_fingerprint
    or portrait_reference (revocation_reason is the one column that's
    correctly NULL for ACTIVE/EXPIRED rows -- see synth/registry.py)."""
    from core.issuer.models import RegistryStatus
    from core.issuer.registry import get_default_registry
    records = get_default_registry().all_records()
    seen_statuses = {r.status for r in records}
    assert seen_statuses == set(RegistryStatus)
    for r in records:
        assert r.portrait_reference, r.registry_record_id
        assert r.document_fingerprint, r.registry_record_id
        assert r.issuer_signature, r.registry_record_id


def test_genuine_document_matches_its_own_registry_record():
    """End-to-end: the actual generated demo passport must find its OWN
    registry record (seeded from the same ground-truth JSON) and pass
    clean -- this is what keeps test_pipeline.py's genuine-is-LOW test
    true now that the issuer check runs on every screening."""
    from core.pipeline import screen_document
    verdict, _ = screen_document(GENUINE)
    issuer_signals = [s for s in verdict.signals if s.tier == Tier.ISSUER]
    assert len(issuer_signals) == 1
    assert issuer_signals[0].severity == Severity.PASS
    assert verdict.band == Band.LOW


# ---------------------------------------------------- registry tampering demo ---

@pytest.mark.skipif(not PATHS["registry_db"].exists(), reason="run `python -m synth.registry` first")
def test_simulate_registry_tampering_is_valid_before_and_compromised_after():
    from ui.actions import simulate_registry_tampering
    result = simulate_registry_tampering()
    assert result["before_ok"] is True
    assert result["after_ok"] is False
    assert result["target_record"] in result["after_detail"]["tampered_record_ids"]


@pytest.mark.skipif(not PATHS["registry_db"].exists(), reason="run `python -m synth.registry` first")
def test_simulate_registry_tampering_never_touches_the_real_registry():
    """The whole point of using a scratch copy: the real, committed
    registry must still verify VALID after the demo runs, and REG-0002
    must still be REVOKED, not silently flipped to ACTIVE."""
    from core.issuer.models import RegistryStatus
    from core.issuer.registry import get_default_registry
    from ui.actions import simulate_registry_tampering

    simulate_registry_tampering()

    registry = get_default_registry()
    ok, _ = registry.verify_integrity()
    assert ok
    record = registry.lookup("900000002")
    assert record.status == RegistryStatus.REVOKED


@pytest.mark.skipif(not PATHS["registry_db"].exists(), reason="run `python -m synth.registry` first")
def test_simulate_registry_tampering_leaves_no_scratch_files_behind():
    from ui.actions import simulate_registry_tampering
    simulate_registry_tampering()
    scratch_dir = PATHS["results"] / "_scratch"
    assert not (scratch_dir / "registry_tamper_demo.db").exists()
    assert not (scratch_dir / "registry_tamper_demo.manifest.json").exists()


# ------------------------------------------------------- Attack Wall scenarios ---
# synth/registry_scenarios.py's two documents: self-consistent, cleanly-signed,
# and caught by NOTHING except the issuer registry -- a different failure
# class from the pixel-forged A/B/C attacks in test_pipeline.py.

REVOKED_DOC = PATHS["documents"] / "demo_revoked_0002.png"
MISMATCH_DOC = PATHS["documents"] / "demo_mismatch_0001.png"
LINKED_DOC = PATHS["documents"] / "demo_linked_0006.png"
STOLEN_DOC = PATHS["documents"] / "demo_stolen_0003.png"
UNREGISTERED_DOC = PATHS["documents"] / "demo_unregistered_0099.png"
EXPIRED_REG_DOC = PATHS["documents"] / "demo_expired_0004.png"
INVALID_DOC = PATHS["documents"] / "demo_invalid_0011.png"

pytestmark_scenarios = pytest.mark.skipif(
    not (REVOKED_DOC.exists() and MISMATCH_DOC.exists() and LINKED_DOC.exists()
         and STOLEN_DOC.exists() and UNREGISTERED_DOC.exists() and EXPIRED_REG_DOC.exists()
         and INVALID_DOC.exists()),
    reason="run `python -m synth.registry_scenarios` first",
)


@pytestmark_scenarios
def test_invalid_scenario_is_critical_via_issuer_alone():
    from core.pipeline import screen_document
    verdict, _ = screen_document(INVALID_DOC)
    assert verdict.band == Band.CRITICAL
    assert verdict.crypto_override is False
    fails = {s.check for s in verdict.signals if s.severity == Severity.FAIL}
    assert fails == {"issuer_status_invalid"}


@pytestmark_scenarios
def test_stolen_scenario_is_critical_via_issuer_alone():
    from core.pipeline import screen_document
    verdict, _ = screen_document(STOLEN_DOC)
    assert verdict.band == Band.CRITICAL
    assert verdict.crypto_override is False
    fails = {s.check for s in verdict.signals if s.severity == Severity.FAIL}
    assert fails == {"issuer_status_stolen"}


@pytestmark_scenarios
def test_unregistered_scenario_never_reads_as_fake_and_stays_low():
    """The honesty invariant, exercised end-to-end: a document number the
    registry has never heard of must not raise the risk band at all --
    NOT_FOUND is WEAK severity, zero weight, by construction."""
    from core.pipeline import screen_document
    verdict, _ = screen_document(UNREGISTERED_DOC)
    assert verdict.band == Band.LOW
    assert verdict.score == 0
    fails = {s.check for s in verdict.signals if s.severity == Severity.FAIL}
    assert fails == set()
    issuer_signal = next(s for s in verdict.signals if s.tier == Tier.ISSUER)
    assert issuer_signal.severity == Severity.WEAK
    assert "could not be established" in issuer_signal.message


@pytestmark_scenarios
def test_registry_expired_scenario_fires_even_though_the_documents_own_dates_are_current():
    """Isolates the registry-level EXPIRED status from the document's own
    expiry_in_past rule: this document's printed dates are current on
    purpose, so expiry_in_past must PASS while issuer_status_expired FAILs."""
    from core.pipeline import screen_document
    verdict, _ = screen_document(EXPIRED_REG_DOC)
    assert verdict.band == Band.CRITICAL
    by_check = {s.check: s for s in verdict.signals}
    assert by_check["expiry_in_past"].severity == Severity.PASS
    assert by_check["issuer_status_expired"].severity == Severity.FAIL


@pytestmark_scenarios
def test_revoked_scenario_is_critical_via_issuer_alone():
    """Every other tier must pass -- if this ever starts failing crosszone
    or crypto too, the scenario document has drifted from REG-0002 and no
    longer demonstrates 'perfect document, revoked registry' cleanly."""
    from core.pipeline import screen_document
    verdict, _ = screen_document(REVOKED_DOC)
    assert verdict.band == Band.CRITICAL
    assert verdict.crypto_override is False  # the registry decided, not crypto
    fails = {s.check for s in verdict.signals if s.severity == Severity.FAIL}
    assert fails == {"issuer_status_revoked"}


@pytestmark_scenarios
def test_mismatch_scenario_is_critical_via_issuer_alone():
    from core.pipeline import screen_document
    verdict, _ = screen_document(MISMATCH_DOC)
    assert verdict.band == Band.CRITICAL
    assert verdict.crypto_override is False
    fails = {s.check for s in verdict.signals if s.severity == Severity.FAIL}
    assert fails == {"issuer_field_mismatch"}


@pytestmark_scenarios
def test_linked_identity_scenario_is_capped_at_high_never_critical():
    """The advisory-tier invariant, exercised end-to-end: a shared
    portrait cluster is serious enough to demand secondary inspection
    (HIGH) but must never, by itself, reach the certainty CRITICAL implies
    -- Tier.IDENTITY is deliberately not in core/risk.py's _DECISIVE_TIERS."""
    from core.pipeline import screen_document
    verdict, _ = screen_document(LINKED_DOC)
    assert verdict.band == Band.HIGH
    assert verdict.band != Band.CRITICAL
    assert verdict.crypto_override is False
    fails = {s.check for s in verdict.signals if s.severity == Severity.FAIL}
    assert fails == {"identity_linkage"}
    linkage = next(s for s in verdict.signals if s.check == "identity_linkage")
    assert linkage.tier == Tier.IDENTITY
    linked_doc_numbers = {l["document_number"] for l in linkage.detail["linked"]}
    assert linked_doc_numbers == {"900000007"}


@pytestmark_scenarios
def test_linked_identity_wording_never_claims_certainty():
    """The spec's own caution, checked as a fact: this must read as
    'possible', never as a positive identification."""
    from core.pipeline import screen_document
    verdict, _ = screen_document(LINKED_DOC)
    linkage = next(s for s in verdict.signals if s.check == "identity_linkage")
    lowered = linkage.message.lower()
    assert "possible" in lowered
    for word in ("confirmed", "certain", "proven", "is the same person"):
        assert word not in lowered


@pytestmark_scenarios
def test_scenario_verdicts_are_never_an_accusation():
    from core.pipeline import screen_document
    accusatory = ["fraud", "criminal", "fake", "liar", "guilty"]
    for path in (REVOKED_DOC, MISMATCH_DOC, LINKED_DOC, STOLEN_DOC, UNREGISTERED_DOC, EXPIRED_REG_DOC,
                  INVALID_DOC):
        verdict, _ = screen_document(path)
        lowered = " ".join(s.message for s in verdict.signals).lower() + verdict.action.lower()
        assert not any(w in lowered for w in accusatory), (path, verdict.action)
