"""Hash-chained, append-only event log: the PS's own "digital trail for
investigations and intelligence analysis" bullet, delivered cryptographically
rather than as a database table someone could quietly edit.

Deliberately NOT a blockchain network, and no PII is ever written here --
see docs/02-STRATEGY.md Thesis 4. Each record stores only a decision, a
digest of its inputs, and metadata.

Two independent guarantees, kept as two functions rather than one, because
they defend against two different attacks:

  verify_chain()          editing any record IN PLACE breaks every hash
                           after it, and names exactly where. Does NOT
                           detect deletion -- a truncated file is fully
                           self-consistent, since nothing after the cut
                           exists to contradict it.

  verify_no_truncation()  catches exactly that gap. append() signs a
                           small {record_count, tail_hash} checkpoint with
                           the same demo signing authority core/crypto/pki.py
                           mints for documents, every time it writes a
                           record. A file with fewer records than the last
                           signed checkpoint claims -- or the right count
                           but a different tail -- can only mean someone
                           deleted the most recent record(s) since that
                           checkpoint was written; producing a checkpoint
                           that agrees with a shorter file requires the
                           signing authority's private key, which a file-
                           level edit does not have.

Both together are still a local hash-chain, not a distributed ledger: an
attacker with the demo signing key AND write access to both files can
regenerate a fully self-consistent shorter chain. That's an honest
boundary of what one local signing authority can attest to on its own,
not a gap in these two functions -- see docs/03-ARCHITECTURE.md's note on
a periodic external anchor for closing it further.
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
    as actually written, including its prev_hash/this_hash.

    Also (re)signs the truncation checkpoint (see module docstring) so it
    always reflects the chain's true current length -- every append moves
    the "how long should this be" attestation forward with it."""
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

    record_count = len(read_all(path))
    _update_checkpoint(path, record_count=record_count, tail_hash=this_hash)
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


def _checkpoint_path(path: Path) -> Path:
    return path.with_suffix(".checkpoint.json")


def _canonical_checkpoint_bytes(checkpoint: dict) -> bytes:
    return json.dumps(checkpoint, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _update_checkpoint(path: Path, record_count: int, tail_hash: str) -> None:
    """Signs {record_count, tail_hash} with the same demo signing authority
    core/crypto/pki.py mints for documents -- one authority attesting both.
    Deferred import: ledger.py otherwise has zero crypto dependency, kept
    that way for every caller (most tests included) that doesn't need
    this."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from core.crypto.pki import load_or_create_pki

    _, dsc_key, dsc_cert = load_or_create_pki()
    checkpoint = {"record_count": record_count, "tail_hash": tail_hash}
    payload = _canonical_checkpoint_bytes(checkpoint)
    signature = dsc_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    signed = {
        "checkpoint": checkpoint,
        "signature": signature.hex(),
        "dsc_cert_pem": dsc_cert.public_bytes(serialization.Encoding.PEM).decode("ascii"),
    }
    _checkpoint_path(path).write_text(json.dumps(signed, indent=2))


def verify_no_truncation(path: str | Path | None = None) -> tuple[bool, dict]:
    """(ok, detail). Compares the ledger's ACTUAL current record count and
    tail hash against the last signed checkpoint append() wrote -- catches
    an attacker deleting the most recent record(s) and stopping, which
    verify_chain() structurally cannot (see this module's docstring).

    Returns (True, {"reason": "no checkpoint on file yet"}) for a ledger
    that predates this feature or has never been written to -- there is
    nothing to compare against, which is not the same claim as "verified
    untruncated"."""
    path = Path(path) if path else PATHS["results"] / "ledger.jsonl"
    checkpoint_path = _checkpoint_path(path)
    if not checkpoint_path.exists():
        return True, {"reason": "no checkpoint on file yet"}

    try:
        signed = json.loads(checkpoint_path.read_text())
    except json.JSONDecodeError:
        return False, {"reason": "checkpoint file is corrupted"}

    from cryptography import x509
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec

    from core.crypto.pki import load_or_create_pki
    from core.crypto.pki import verify_chain as verify_pki_chain

    csca_cert, _, _ = load_or_create_pki()
    try:
        dsc_cert = x509.load_pem_x509_certificate(signed["dsc_cert_pem"].encode("ascii"))
        if not verify_pki_chain(dsc_cert, csca_cert):
            return False, {"reason": "checkpoint signer certificate is not trusted"}
        payload = _canonical_checkpoint_bytes(signed["checkpoint"])
        dsc_cert.public_key().verify(bytes.fromhex(signed["signature"]), payload, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False, {"reason": "checkpoint signature is invalid"}
    except Exception as e:
        return False, {"reason": f"checkpoint is malformed ({type(e).__name__})"}

    expected = signed["checkpoint"]
    records = read_all(path)
    actual_count = len(records)
    actual_tail = records[-1]["this_hash"] if records else GENESIS_HASH

    if actual_count < expected["record_count"]:
        return False, {"reason": "AUDIT HISTORY TRUNCATION DETECTED", "detail":
                        f"expected at least {expected['record_count']} records, found {actual_count}",
                        "expected_count": expected["record_count"], "actual_count": actual_count}
    if actual_count == expected["record_count"] and actual_tail != expected["tail_hash"]:
        return False, {"reason": "AUDIT HISTORY TRUNCATION DETECTED", "detail":
                        "record count matches but the most recent record's fingerprint does not -- "
                        "it was replaced, not merely followed by new ones",
                        "expected_count": expected["record_count"], "actual_count": actual_count}
    return True, {"expected_count": expected["record_count"], "actual_count": actual_count}