"""Demo signing authority: a real, if simplified, two-level X.509 chain --
a self-signed root (standing in for a country's CSCA, Country Signing CA)
and a Document Signer Certificate issued by that root (standing in for a
country's DSC, which actually signs each document's data in a real
eMRTD). ECDSA P-256 throughout.

This is explicitly NOT the ICAO PKD: a real inspection system chains to
certificates published through ICAO's Public Key Directory, which this
project has no access to and does not claim to. Labelled everywhere it
surfaces (see core/crypto/manifest.py, ui/) as a demo signing authority.
The cryptography itself -- key generation, certificate issuance, chain
verification, signing, signature verification -- is real; only the trust
anchor is our own, not a government's.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from config import PATHS

CURVE = ec.SECP256R1()
VALIDITY_DAYS = 3650


def _subject(common_name: str) -> x509.Name:
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "UT"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "UTOPIA Demo Signing Authority"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])


def generate_csca() -> tuple[ec.EllipticCurvePrivateKey, x509.Certificate]:
    """Self-signed root: stands in for a country's CSCA."""
    key = ec.generate_private_key(CURVE)
    subject = issuer = _subject("UTO Demo CSCA")
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject).issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now).not_valid_after(now + dt.timedelta(days=VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=False, content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True,
            encipher_only=False, decipher_only=False), critical=True)
        .sign(key, hashes.SHA256())
    )
    return key, cert


def generate_dsc(csca_key: ec.EllipticCurvePrivateKey, csca_cert: x509.Certificate
                  ) -> tuple[ec.EllipticCurvePrivateKey, x509.Certificate]:
    """Document Signer Certificate: issued BY the CSCA, used to sign
    individual documents -- never used to issue further certificates."""
    key = ec.generate_private_key(CURVE)
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(_subject("UTO Demo DSC")).issuer_name(csca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now).not_valid_after(now + dt.timedelta(days=VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True, content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
            encipher_only=False, decipher_only=False), critical=True)
        .sign(csca_key, hashes.SHA256())
    )
    return key, cert


def verify_chain(dsc_cert: x509.Certificate, csca_cert: x509.Certificate) -> bool:
    """Confirms the DSC's signature was actually produced by the CSCA's
    private key -- the chain-of-trust check, not just "is this a cert".

    Pins SHA-256 explicitly rather than trusting dsc_cert's own declared
    signature_hash_algorithm: this CSCA only ever signs a DSC it generated
    itself with a hardcoded SHA-256 (generate_dsc, above), so there is no
    live attack today, but a verifier should never let the certificate
    under test choose which algorithm verifies it -- that is exactly the
    shape of a hash-confusion downgrade if this function is ever reused
    against a less-trusted input.
    """
    try:
        csca_cert.public_key().verify(
            dsc_cert.signature, dsc_cert.tbs_certificate_bytes, ec.ECDSA(hashes.SHA256()),
        )
        return True
    except Exception:
        return False


def _write_key(path: Path, key: ec.EllipticCurvePrivateKey) -> None:
    path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))


def _read_key(path: Path) -> ec.EllipticCurvePrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def load_or_create_pki() -> tuple[x509.Certificate, ec.EllipticCurvePrivateKey, x509.Certificate]:
    """Persists to data/pki/ (gitignored) so repeated runs reuse the same
    demo authority instead of minting a new one every process start --
    otherwise every previously-signed manifest would fail chain
    verification the moment the process restarted."""
    pki_dir = PATHS["pki"]
    pki_dir.mkdir(parents=True, exist_ok=True)
    csca_key_p, csca_cert_p = pki_dir / "csca_key.pem", pki_dir / "csca_cert.pem"
    dsc_key_p, dsc_cert_p = pki_dir / "dsc_key.pem", pki_dir / "dsc_cert.pem"

    if all(p.exists() for p in (csca_key_p, csca_cert_p, dsc_key_p, dsc_cert_p)):
        csca_cert = x509.load_pem_x509_certificate(csca_cert_p.read_bytes())
        dsc_key = _read_key(dsc_key_p)
        dsc_cert = x509.load_pem_x509_certificate(dsc_cert_p.read_bytes())
        return csca_cert, dsc_key, dsc_cert

    csca_key, csca_cert = generate_csca()
    dsc_key, dsc_cert = generate_dsc(csca_key, csca_cert)
    _write_key(csca_key_p, csca_key)
    csca_cert_p.write_bytes(csca_cert.public_bytes(serialization.Encoding.PEM))
    _write_key(dsc_key_p, dsc_key)
    dsc_cert_p.write_bytes(dsc_cert.public_bytes(serialization.Encoding.PEM))
    return csca_cert, dsc_key, dsc_cert


if __name__ == "__main__":
    csca_cert, dsc_key, dsc_cert = load_or_create_pki()
    print("CSCA subject:", csca_cert.subject.rfc4514_string())
    print("DSC subject: ", dsc_cert.subject.rfc4514_string())
    print("chain valid: ", verify_chain(dsc_cert, csca_cert))
