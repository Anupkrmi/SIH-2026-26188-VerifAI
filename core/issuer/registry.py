"""Synthetic / Demonstration Issuer Registry -- a SQLite-backed stand-in
for what an authorized government or institutional issuer registry
connector would provide. This is NOT a connection to Passport Seva,
UIDAI, DigiLocker, INTERPOL, or any real government system; every record
here is generated synthetic data (see synth/registry.py). Label this
plainly ("Synthetic Issuer Registry / Demo Issuance Authority") everywhere
it surfaces in the UI.

Implements core.issuer.models.IssuerRegistryProvider -- a future real
connector (GovernmentIssuerRegistry, DigiLockerProvider,
AuthorizedBorderDatabase) is a drop-in replacement behind the same
lookup()/verify_integrity()/stats() shape; nothing in core/pipeline.py or
the UI needs to know which one it's talking to.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path

from config import PATHS
from core.issuer.integrity import (
    aggregate_fingerprint, load_manifest, record_fingerprint, sign_manifest,
    verify_manifest, write_manifest,
)
from core.issuer.models import RegistryRecord, RegistryStatus

_COLUMNS = [
    "registry_record_id", "document_number", "document_type", "issuer_id", "person_id",
    "name", "date_of_birth", "nationality", "issue_date", "expiry_date", "status",
    "revocation_reason", "portrait_reference", "document_fingerprint", "created_at",
    "issuer_signature",
]


def _row_to_record(row: sqlite3.Row) -> RegistryRecord:
    return RegistryRecord(
        registry_record_id=row["registry_record_id"],
        document_number=row["document_number"],
        document_type=row["document_type"],
        issuer_id=row["issuer_id"],
        person_id=row["person_id"],
        name=row["name"],
        date_of_birth=date.fromisoformat(row["date_of_birth"]),
        nationality=row["nationality"],
        issue_date=date.fromisoformat(row["issue_date"]),
        expiry_date=date.fromisoformat(row["expiry_date"]),
        status=RegistryStatus(row["status"]),
        revocation_reason=row["revocation_reason"],
        portrait_reference=row["portrait_reference"],
        document_fingerprint=row["document_fingerprint"],
        created_at=datetime.fromisoformat(row["created_at"]),
        issuer_signature=row["issuer_signature"],
    )


def init_db(db_path: str | Path) -> None:
    """Creates the table if it doesn't exist yet. Safe to call repeatedly --
    synth/registry.py calls this before (re)seeding."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                registry_record_id TEXT PRIMARY KEY,
                document_number TEXT NOT NULL,
                document_type TEXT NOT NULL,
                issuer_id TEXT NOT NULL,
                person_id TEXT NOT NULL,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                nationality TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                status TEXT NOT NULL,
                revocation_reason TEXT,
                portrait_reference TEXT,
                document_fingerprint TEXT,
                created_at TEXT NOT NULL,
                issuer_signature TEXT NOT NULL
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_document_number ON records(document_number)")
        conn.commit()
    finally:
        conn.close()


def insert_record(db_path: str | Path, record: RegistryRecord) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            f"INSERT OR REPLACE INTO records ({', '.join(_COLUMNS)}) "
            f"VALUES ({', '.join('?' * len(_COLUMNS))})",
            [
                record.registry_record_id, record.document_number, record.document_type,
                record.issuer_id, record.person_id, record.name,
                record.date_of_birth.isoformat(), record.nationality,
                record.issue_date.isoformat(), record.expiry_date.isoformat(),
                record.status.value, record.revocation_reason, record.portrait_reference,
                record.document_fingerprint, record.created_at.isoformat(), record.issuer_signature,
            ],
        )
        conn.commit()
    finally:
        conn.close()


class SyntheticIssuerRegistry:
    """Read-mostly: every call opens a short-lived connection, matching how
    infrequently a screening actually hits this (once per document) -- no
    pooling machinery a demo has no use for."""

    def __init__(self, db_path: str | Path, manifest_path: str | Path):
        self.db_path = Path(db_path)
        self.manifest_path = Path(manifest_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def lookup(self, document_number: str) -> RegistryRecord | None:
        if not self.db_path.exists():
            return None
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM records WHERE document_number = ?", (document_number,)
            ).fetchone()
            return _row_to_record(row) if row else None
        finally:
            conn.close()

    def all_records(self) -> list[RegistryRecord]:
        if not self.db_path.exists():
            return []
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM records ORDER BY registry_record_id").fetchall()
            return [_row_to_record(r) for r in rows]
        finally:
            conn.close()

    def find_linked_records(self, portrait_reference: str | None, exclude_record_id: str
                              ) -> list[RegistryRecord]:
        """Other registry records sharing the same portrait cluster -- the
        seed data's stand-in for "this biometric identity has been issued
        more than one credential" (see synth/registry.py's
        REG-0006/REG-0007). A synthetic symbolic label, not a real face
        embedding comparison -- see core/issuer/models.py."""
        if not portrait_reference or not self.db_path.exists():
            return []
        return [r for r in self.all_records()
                if r.portrait_reference == portrait_reference and r.registry_record_id != exclude_record_id]

    def stats(self) -> dict[str, int]:
        records = self.all_records()
        counts = {status.value: 0 for status in RegistryStatus}
        for r in records:
            counts[r.status.value] += 1
        counts["TOTAL"] = len(records)
        return counts

    def ensure_signed(self) -> dict:
        """Lazily (re)signs the manifest with whatever demo PKI exists on
        THIS machine (created if needed) -- mirrors
        core/crypto/pki.py::load_or_create_pki's own lazy-init pattern.
        Re-signs whenever the registry's own aggregate fingerprint no
        longer matches what's on file (first run, or the record set
        changed), so a stale manifest never silently masks a real edit."""
        from core.crypto.pki import load_or_create_pki
        records = self.all_records()
        aggregate = aggregate_fingerprint([r.issuer_signature for r in records])
        existing = load_manifest(self.manifest_path)
        if existing and existing.get("manifest", {}).get("aggregate_sha256") == aggregate:
            return existing
        csca_cert, dsc_key, dsc_cert = load_or_create_pki()
        signed = sign_manifest(aggregate, len(records),
                                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                dsc_key, dsc_cert)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        write_manifest(signed, self.manifest_path)
        return signed

    def verify_integrity(self) -> tuple[bool, dict]:
        """(valid, detail). detail always carries record_count and, on
        failure, exactly which check failed -- a hand-edited row's
        fingerprint no longer matching its stored issuer_signature is
        reported BEFORE the signature check even runs, since that is the
        more specific, more actionable finding (this is the check the
        REVOKED -> ACTIVE tamper demo in synth/registry.py's docstring
        depends on)."""
        records = self.all_records()
        tampered = [r.registry_record_id for r in records if record_fingerprint(r) != r.issuer_signature]
        if tampered:
            return False, {"reason": "One or more registry records were modified without a valid "
                                       "issuer signature", "tampered_record_ids": tampered,
                            "record_count": len(records)}

        from core.crypto.pki import load_or_create_pki
        csca_cert, _, _ = load_or_create_pki()
        signed = self.ensure_signed()
        aggregate = aggregate_fingerprint([r.issuer_signature for r in records])
        if signed["manifest"]["aggregate_sha256"] != aggregate:
            return False, {"reason": "Registry contents do not match the signed manifest",
                            "record_count": len(records)}
        ok, reason = verify_manifest(signed, csca_cert)
        return ok, {"reason": reason, "record_count": len(records)}


@lru_cache(maxsize=1)
def get_default_registry() -> SyntheticIssuerRegistry:
    return SyntheticIssuerRegistry(PATHS["registry_db"], PATHS["registry_manifest"])