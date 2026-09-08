"""One-shot smoke test: every database/file-backed connection this app
depends on, exercised for real. Not a replacement for tests/ (that's the
correctness suite) -- this is the fast, human-readable "is everything
actually wired up right now" check, meant to be run before a demo.

    python -m scripts.smoke_test
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from config import PATHS


def _check(label: str, fn) -> bool:
    try:
        detail = fn()
        print(f"[PASS] {label}" + (f" -- {detail}" if detail else ""))
        return True
    except Exception as e:
        print(f"[FAIL] {label} -- {type(e).__name__}: {e}")
        return False


def check_registry_db() -> str:
    from core.issuer.registry import get_default_registry
    registry = get_default_registry()
    if not registry.db_path.exists():
        raise RuntimeError(f"{registry.db_path} does not exist -- run `python -m synth.registry`")
    records = registry.all_records()
    if not records:
        raise RuntimeError("registry.db connected but returned 0 records")
    ok, detail = registry.verify_integrity()
    if not ok:
        raise RuntimeError(f"registry integrity check failed: {detail}")
    return f"{len(records)} records, integrity: {detail['reason']}"


def check_registry_lookup() -> str:
    from core.issuer.registry import get_default_registry
    record = get_default_registry().lookup("181960013")
    if record is None:
        raise RuntimeError("lookup('181960013') returned None -- expected REG-0001")
    return f"found {record.registry_record_id} ({record.name}, status {record.status.value})"


def check_registry_linkage() -> str:
    from core.issuer.registry import get_default_registry
    registry = get_default_registry()
    linked = registry.find_linked_records("PORTRAIT-CLUSTER-07", exclude_record_id="REG-0006")
    if not linked:
        raise RuntimeError("expected REG-0007 linked to REG-0006 via PORTRAIT-CLUSTER-07, found none")
    return f"REG-0006 linked to {[r.registry_record_id for r in linked]}"


def check_ledger_roundtrip() -> str:
    from core.crypto import ledger
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "smoke_ledger.jsonl"
        for i in range(3):
            ledger.append({"case_id": f"smoke_{i}", "band": "LOW"}, path=path)
        chain_ok, _ = ledger.verify_chain(path)
        trunc_ok, _ = ledger.verify_no_truncation(path)
        if not (chain_ok and trunc_ok):
            raise RuntimeError(f"chain_ok={chain_ok} trunc_ok={trunc_ok}")
    return "append -> verify_chain -> verify_no_truncation round-trip clean"


def check_pipeline_end_to_end() -> str:
    from core.pipeline import screen_document
    genuine = PATHS["documents"] / "demo_0001.png"
    if not genuine.exists():
        raise RuntimeError(f"{genuine} does not exist -- run `python -m synth.passport`")
    verdict, _ = screen_document(genuine)
    if verdict.band.value != "LOW":
        raise RuntimeError(f"expected the genuine document to score LOW, got {verdict.band.value}")
    return f"band={verdict.band.value} score={verdict.score}"


def main() -> int:
    checks = [
        ("Issuer registry DB connects and has data", check_registry_db),
        ("Issuer registry lookup finds the genuine record", check_registry_lookup),
        ("Issuer registry linkage cross-reference works", check_registry_linkage),
        ("Ledger append/verify round-trip (scratch path)", check_ledger_roundtrip),
        ("Full pipeline runs end-to-end on the genuine document", check_pipeline_end_to_end),
    ]
    results = [_check(label, fn) for label, fn in checks]
    print()
    if all(results):
        print(f"ALL {len(results)} CHECKS PASSED")
        return 0
    print(f"{results.count(False)}/{len(results)} CHECKS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
