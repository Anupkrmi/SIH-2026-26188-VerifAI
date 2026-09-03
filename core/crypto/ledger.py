"""Hash-chained, append-only event log: the PS's own "digital trail for
investigations and intelligence analysis" bullet, delivered cryptographically
rather than as a database table someone could quietly edit.

Deliberately NOT a blockchain network, and no PII is ever written here --
see docs/02-STRATEGY.md Thesis 4. Each record stores only a decision, a
digest of its inputs, and metadata.

What this actually guarantees, stated precisely after a security review
caught an overclaim in an earlier version of this docstring: editing any
record IN PLACE breaks every hash after it, and verify_chain() names
exactly where. It does NOT, on its own, detect an attacker who deletes
the most recent record(s) and stops -- a truncated file is fully
self-consistent, since nothing after the cut exists to contradict it, and
someone with local write access could equally regenerate an entirely
different chain from GENESIS_HASH. Closing that gap needs an external
attestation of how long the chain SHOULD be -- e.g. the periodic
Merkle-root anchor to a permissioned ledger docs/03-ARCHITECTURE.md
already calls for -- which is not yet implemented. Local file integrity
against tampering with existing records is real today; tamper-evidence
against a truncation attack is future work, not a guarantee this module
currently makes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from config import PATHS

GENESIS_HASH = "0" * 64


def _record_hash(prev_hash: str, record_without_hash: dict) -> str:
    payload = json.dumps({**record_without_hash, "prev_hash": prev_hash}, sort_keys=True,
                          separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append(record: dict, path: str | Path | None = None) -> dict:
    """record should carry no PII -- case_id, decision/band, model
    version, an input digest, officer id, timestamp. Returns the record
    as actually written, including its prev_hash/this_hash."""
    path = Path(path) if path else PATHS["results"] / "ledger.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)

    prev_hash = GENESIS_HASH
    if path.exists() and path.stat().st_size > 0:
        with open(path, "rb") as f:
            last_line = f.readlines()[-1]
        try:
            prev_hash = json.loads(last_line)["this_hash"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"ledger at {path} ends in a corrupted record; "
                              f"cannot safely determine prev_hash to append after it") from e

    this_hash = _record_hash(prev_hash, record)
    full_record = {**record, "prev_hash": prev_hash, "this_hash": this_hash}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(full_record, sort_keys=True) + "\n")
    return full_record


def read_all(path: str | Path | None = None) -> list[dict]:
    """Records in append order, malformed lines included as-is (a
    JSONDecodeError here should surface to whoever is displaying the
    ledger, not be swallowed) -- read-only, does not affect
    verify_chain's own tamper detection."""
    path = Path(path) if path else PATHS["results"] / "ledger.jsonl"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def verify_chain(path: str | Path | None = None) -> tuple[bool, int | None]:
    """Returns (ok, broken_at_index). broken_at_index is the 0-based index
    of the first record whose stored hash no longer matches what its own
    content and declared prev_hash recompute to -- naming exactly where an
    edit happened, not just that the file is "wrong" somewhere."""
    path = Path(path) if path else PATHS["results"] / "ledger.jsonl"
    if not path.exists():
        return True, None

    expected_prev = GENESIS_HASH
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                return False, i  # an unparseable record is not verifiable, full stop
            stored_prev = record.get("prev_hash")
            stored_this = record.get("this_hash")
            content = {k: v for k, v in record.items() if k not in ("prev_hash", "this_hash")}
            recomputed = _record_hash(stored_prev, content)
            if stored_prev != expected_prev or stored_this != recomputed:
                return False, i
            expected_prev = stored_this
    return True, None
