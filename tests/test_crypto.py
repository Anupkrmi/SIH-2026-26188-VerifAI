"""core/crypto/*.py acceptance tests: chain issuance, the two verification
modes (self-consistency vs impersonation), tamper detection on both the
signed manifest and the ledger. See core/crypto/manifest.py's module
docstring for why self-consistency and impersonation are deliberately
different checks, not the same one applied twice.
"""
import json
from pathlib import Path

import pytest

from config import PATHS
from core.crypto import ledger
from core.crypto.manifest import sign_document, verify_document
from core.crypto.pki import generate_csca, generate_dsc, verify_chain
from core.types import Severity

GENUINE = PATHS["documents"] / "demo_0001.png"
ATTACK_A = PATHS["forged"] / "forged_demo_0001_A.png"
ATTACK_B = PATHS["forged"] / "forged_demo_0001_B.png"
ATTACK_C = PATHS["forged"] / "forged_demo_0001_C.png"

pytestmark = pytest.mark.skipif(
    not GENUINE.exists(), reason="run `python -m synth.passport && python -m synth.forge` first"
)


@pytest.fixture(scope="module")
def pki():
    csca_key, csca_cert = generate_csca()
    dsc_key, dsc_cert = generate_dsc(csca_key, csca_cert)
    return csca_cert, dsc_key, dsc_cert


def test_dsc_chains_to_csca(pki):
    csca_cert, dsc_key, dsc_cert = pki
    assert verify_chain(dsc_cert, csca_cert)


def test_dsc_does_not_chain_to_an_unrelated_root(pki):
    csca_cert, dsc_key, dsc_cert = pki
    other_csca_key, other_csca_cert = generate_csca()
    assert not verify_chain(dsc_cert, other_csca_cert)


def test_self_consistency_passes_for_an_untouched_document(pki):
    csca_cert, dsc_key, dsc_cert = pki
    sod = sign_document(GENUINE, dsc_key, dsc_cert)
    signal = verify_document(GENUINE, sod, csca_cert)
    assert signal.severity == Severity.PASS


def test_self_consistency_passes_even_for_attacks_crypto_cannot_see(pki):
    """DOB edit and screen recapture both alter the ORIGINAL capture, not
    a stored record after the fact -- signing each fresh at intake and
    verifying against that same signature must PASS. Crosszone and
    forensics are what catch these, not crypto; see the module docstring."""
    csca_cert, dsc_key, dsc_cert = pki
    for path in (ATTACK_A, ATTACK_C):
        sod = sign_document(path, dsc_key, dsc_cert)
        signal = verify_document(path, sod, csca_cert)
        assert signal.severity == Severity.PASS, path


def test_impersonation_is_caught_by_portrait_hash_mismatch(pki):
    """The flagship demo: sign the genuine document, then present the
    portrait-swapped attack claiming to be that same signed record."""
    csca_cert, dsc_key, dsc_cert = pki
    genuine_sod = sign_document(GENUINE, dsc_key, dsc_cert)
    signal = verify_document(ATTACK_B, genuine_sod, csca_cert)
    assert signal.severity == Severity.FAIL
    assert "portrait_sha256" in signal.detail["changed_fields"]


def test_hand_edited_manifest_fails_signature_check(pki):
    csca_cert, dsc_key, dsc_cert = pki
    sod = sign_document(GENUINE, dsc_key, dsc_cert)
    tampered = json.loads(json.dumps(sod))
    tampered["manifest"]["portrait_sha256"] = "0" * 64
    signal = verify_document(GENUINE, tampered, csca_cert)
    assert signal.severity == Severity.FAIL


def test_ledger_read_all_returns_records_in_append_order(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    for i in range(3):
        ledger.append({"case_id": f"case_{i:03d}"}, path=path)
    records = ledger.read_all(path)
    assert [r["case_id"] for r in records] == ["case_000", "case_001", "case_002"]


def test_ledger_read_all_on_missing_file_returns_empty_list(tmp_path: Path):
    assert ledger.read_all(tmp_path / "does_not_exist.jsonl") == []


def test_ledger_verifies_clean(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    for i in range(5):
        ledger.append({"case_id": f"case_{i:03d}", "band": "LOW"}, path=path)
    ok, broken_at = ledger.verify_chain(path)
    assert ok
    assert broken_at is None


def test_ledger_names_the_exact_tampered_record(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    for i in range(5):
        ledger.append({"case_id": f"case_{i:03d}", "band": "LOW"}, path=path)

    lines = path.read_text().splitlines()
    record = json.loads(lines[2])
    record["band"] = "CRITICAL"  # an attacker rewrites a past verdict
    lines[2] = json.dumps(record, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")

    ok, broken_at = ledger.verify_chain(path)
    assert not ok
    assert broken_at == 2


def test_ledger_verify_reports_corrupted_line_rather_than_crashing(tmp_path: Path):
    """Found in security review: a corrupted/truncated last write (e.g. a
    crash mid-append) must be reported as a broken record, not raise an
    unhandled JSONDecodeError up through the caller."""
    path = tmp_path / "ledger.jsonl"
    ledger.append({"case_id": "case_000"}, path=path)
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"case_id": "case_001", "not valid json' + "\n")
    ok, broken_at = ledger.verify_chain(path)
    assert not ok
    assert broken_at == 1


def test_ledger_append_refuses_to_extend_a_corrupted_chain(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    path.write_text('{"case_id": "case_000", "not valid json\n')
    with pytest.raises(ValueError):
        ledger.append({"case_id": "case_001"}, path=path)


def test_ledger_never_stores_pii_by_construction():
    """Structural check on the docstring's own promise: append() takes
    exactly the caller's dict plus prev_hash/this_hash -- it has no field
    for names, document numbers, or biometric templates to accidentally
    end up in. This test documents the contract; it cannot stop a caller
    from choosing to pass PII in, which is a call-site discipline, not
    something this module can enforce for them.
    """
    import inspect
    sig = inspect.signature(ledger.append)
    assert set(sig.parameters) == {"record", "path"}
