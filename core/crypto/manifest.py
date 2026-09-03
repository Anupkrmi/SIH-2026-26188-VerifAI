"""Canonical manifest: sign the document's portrait and MRZ pixel hashes
at intake, verify them later. Simplified from full ICAO Passive
Authentication (which hashes every data group on a chip) to exactly two
hashes, but the cryptographic property is the same one PA provides: proof
that specific data has not changed since a trusted authority attested to
it.

What this legitimately proves vs does not, stated precisely because it
matters for the demo narrative:

  PROVES: the portrait and MRZ pixels in the presented image are
  byte-identical to what was signed at intake -- i.e. nothing has altered
  OUR OWN STORED RECORD since we captured and signed it. This is the
  injection-attack defence (docs/01-RESEARCH.md): if an attacker
  substitutes an image after our system attested to the original, the
  hash mismatch is immediate and needs no model.

  DOES NOT PROVE: that the original capture itself was a genuine document
  rather than, say, a photograph of a screen. A screen recapture gets
  signed too, faithfully, at the moment it is captured -- there is nothing
  for a hash check to disagree with, because nothing has been altered
  SINCE that signature was made. That is exactly why
  core/forensics/recapture.py exists as an independent signal: cryptography
  answers "has this record been tampered with since intake", not
  "was intake itself trustworthy". Conflating the two would be dishonest.

This is why the pipeline offers two distinct verification modes:
  - self-consistency: sign the presented image, then immediately verify
    it against that same signature. Used for attacks that alter the
    ORIGINAL capture (DOB edit, screen recapture) -- crypto correctly
    stays silent; the tier built to catch each of those (crosszone,
    forensics) is the one that fires.
  - impersonation: verify a presented image against a DIFFERENT, earlier
    signature -- simulating an attacker substituting a photo on what is
    presented as a previously-issued, already-signed record. Used for the
    portrait-swap attack, which is precisely that scenario.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from core.crypto.pki import verify_chain
from core.fields import MRZ_BAND_BBOX, PORTRAIT_BBOX, crop
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_manifest(gray) -> dict:
    portrait = crop(gray, PORTRAIT_BBOX)
    mrz_band = crop(gray, MRZ_BAND_BBOX, is_xywh=True)
    return {
        "portrait_sha256": _sha256(portrait.tobytes()),
        "mrz_sha256": _sha256(mrz_band.tobytes()),
    }


def _canonical_bytes(manifest: dict) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_document(image_path: str | Path, dsc_key: ec.EllipticCurvePrivateKey,
                   dsc_cert: x509.Certificate) -> dict:
    """The intake-time step: compute the manifest, sign it, package it
    with the DSC certificate so a verifier doesn't need separate access to
    the signing authority's cert store."""
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    manifest = compute_manifest(gray)
    payload = _canonical_bytes(manifest)
    signature = dsc_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    return {
        "manifest": manifest,
        "signature": signature.hex(),
        "dsc_cert_pem": dsc_cert.public_bytes(serialization.Encoding.PEM).decode("ascii"),
    }


def write_sod(sod: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(sod, indent=2))


def load_sod(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def verify_document(image_path: str | Path, sod: dict, csca_cert: x509.Certificate,
                     policy: dict | None = None) -> Signal:
    """Recompute the manifest from the PRESENTED image's actual pixels and
    check it against the signed one. This is the decisive T0 tier: see
    core/risk.py -- an invalid result here forces CRITICAL regardless of
    every other signal, with no model consulted for that decision."""
    policy = policy or load_policy()

    # sod is attacker-reachable input by construction (it is exactly what
    # the "impersonation" mode is designed to receive alongside a forged
    # image), so every parsing step here needs to fail closed with a clean
    # Signal rather than an uncaught exception -- a malformed dsc_cert_pem,
    # non-hex signature, or missing key must read as CRITICAL, not crash
    # the pipeline. Caught broadly, matching core/crypto/pki.py's
    # verify_chain, rather than only the one exception type the crypto
    # library itself raises for the specific case we control.
    try:
        dsc_cert = x509.load_pem_x509_certificate(sod["dsc_cert_pem"].encode("ascii"))
        if not verify_chain(dsc_cert, csca_cert):
            return Signal(tier=Tier.CRYPTO, check="signature_chain", severity=Severity.FAIL, weight=100,
                           message="Document Signer certificate was not issued by the trusted signing authority")

        signed_manifest = sod["manifest"]
        payload = _canonical_bytes(signed_manifest)
        dsc_cert.public_key().verify(bytes.fromhex(sod["signature"]), payload, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return Signal(tier=Tier.CRYPTO, check="signature_valid", severity=Severity.FAIL, weight=100,
                       message="Signature does not match the signed manifest -- the record itself is invalid")
    except Exception as e:
        return Signal(tier=Tier.CRYPTO, check="signature_valid", severity=Severity.FAIL, weight=100,
                       message=f"Signed record is malformed and could not be verified ({type(e).__name__})")

    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    presented_manifest = compute_manifest(gray)
    if presented_manifest != signed_manifest:
        changed = [k for k in signed_manifest if signed_manifest[k] != presented_manifest.get(k)]
        return Signal(
            tier=Tier.CRYPTO, check="manifest_match", severity=Severity.FAIL, weight=100,
            message=f"Signed document data has been modified since it was signed ({', '.join(changed)})",
            detail={"changed_fields": changed},
        )

    return Signal(tier=Tier.CRYPTO, check="manifest_match", severity=Severity.PASS, weight=0,
                   message="Presented document matches its signed record exactly; signature chain verified "
                            "(demo signing authority -- see core/crypto/pki.py)")


def resolve_and_verify(image_path: str | Path, csca_cert: x509.Certificate,
                        policy: dict | None = None) -> Signal | None:
    """Looks for a signed record for this exact image (a "<image>.sod.json"
    sidecar -- the self-consistency case), and failing that, for a forged_*
    attack's own metadata naming which OTHER document's signature it should
    be checked against (the impersonation case; see synth/sign.py).
    Returns None if no signed record exists or applies at all -- meaning
    no crypto tier was evaluated, not that it passed.
    """
    image_path = Path(image_path)
    own_sod = image_path.with_suffix(".sod.json")
    if own_sod.exists():
        return verify_document(image_path, load_sod(own_sod), csca_cert, policy=policy)

    meta_path = image_path.with_suffix(".json")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("crypto_mode") == "impersonation" and "source_doc" in meta:
            reference_sod = image_path.parent.parent / "documents" / f"{meta['source_doc']}.sod.json"
            if reference_sod.exists():
                return verify_document(image_path, load_sod(reference_sod), csca_cert, policy=policy)
    return None
