"""Registry integrity: per-record fingerprints + a signed aggregate
manifest, reusing the SAME demo signing authority core/crypto/pki.py
already mints for documents -- one authority attesting both.

Deliberately not per-record ECDSA signatures. Each record's
`issuer_signature` is a sha256 fingerprint of its own canonical fields --
cheap, key-independent, identical on every machine. The manifest
aggregates those fingerprints into one sha256 ("aggregate_sha256", a
simplified Merkle-root stand-in: sorted-fingerprint concatenation, not a
full tree) and THAT is what gets ECDSA-signed. Flipping a status in place
(e.g. REVOKED -> ACTIVE) changes that row's fingerprint and the aggregate
hash, so core/issuer/registry.py::verify_integrity() catches it without a
real Merkle tree.

Why the manifest is never committed to git: data/pki/'s keys are
per-machine and non-deterministic (core/crypto/pki.py::generate_csca has
no seed) -- a manifest signed on one machine would fail signature-chain
verification against a DIFFERENT machine's freshly-generated CSCA. Signing
lazily, on whatever PKI already exists (or gets lazily created) on the
machine that's actually running, keeps the mint and the verify always
talking to the same authority -- see load_or_create_pki's own docstring
for the identical reasoning applied to documents.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.issuer.models import RegistryRecord


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def record_fingerprint(record: RegistryRecord) -> str:
    """sha256 over every field EXCEPT issuer_signature itself -- a hand
    edit to any other column (status included) changes this."""
    payload = record.model_dump(mode="json", exclude={"issuer_signature"})
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def aggregate_fingerprint(fingerprints: list[str]) -> str:
    return hashlib.sha256(",".join(sorted(fingerprints)).encode("utf-8")).hexdigest()


def sign_manifest(aggregate_sha256: str, record_count: int, generated_at: str,
                   dsc_key: ec.EllipticCurvePrivateKey, dsc_cert: x509.Certificate) -> dict:
    manifest = {"record_count": record_count, "generated_at": generated_at,
                "aggregate_sha256": aggregate_sha256}
    payload = _canonical_bytes(manifest)
    signature = dsc_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    return {
        "manifest": manifest,
        "signature": signature.hex(),
        "dsc_cert_pem": dsc_cert.public_bytes(serialization.Encoding.PEM).decode("ascii"),
    }


def write_manifest(signed: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(signed, indent=2))


def load_manifest(path: str | Path) -> dict | None:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def verify_manifest(signed: dict, csca_cert: x509.Certificate) -> tuple[bool, str]:
    """(valid, reason). Mirrors core/crypto/manifest.py::verify_document's
    fail-closed shape: any parse/verification problem is a clean False,
    never an uncaught exception."""
    from core.crypto.pki import verify_chain
    try:
        dsc_cert = x509.load_pem_x509_certificate(signed["dsc_cert_pem"].encode("ascii"))
        if not verify_chain(dsc_cert, csca_cert):
            return False, "Document Signer certificate was not issued by the trusted signing authority"
        payload = _canonical_bytes(signed["manifest"])
        dsc_cert.public_key().verify(bytes.fromhex(signed["signature"]), payload, ec.ECDSA(hashes.SHA256()))
        return True, "Signature valid"
    except InvalidSignature:
        return False, "Manifest signature does not match its signed content"
    except Exception as e:
        return False, f"Manifest is malformed and could not be verified ({type(e).__name__})"