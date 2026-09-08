"""Data contracts for the Synthetic Issuer Registry.

NOT a connection to any real government database -- see
core/issuer/registry.py's module docstring. This models what an
authorized issuer/registry connector would plausibly return, so a future
real connector (GovernmentIssuerRegistry, DigiLockerProvider, ...) can
implement the same IssuerRegistryProvider shape with no caller change.
"""
from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Protocol

from pydantic import BaseModel


class RegistryStatus(str, Enum):
    """Stored status values. NOT_FOUND is deliberately absent here -- it is
    never a row in the database, it's what lookup() returns (None) when no
    row matches at all. See core/issuer/compare.py for why that distinction
    matters (never read "no record" as "fake")."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    STOLEN = "STOLEN"
    INVALID = "INVALID"


class RegistryRecord(BaseModel):
    registry_record_id: str
    document_number: str
    document_type: str
    issuer_id: str
    person_id: str
    name: str
    date_of_birth: dt.date
    nationality: str
    issue_date: dt.date
    expiry_date: dt.date
    status: RegistryStatus
    revocation_reason: str | None = None
    # Reserved for a future biometric-linkage / document-binding pass
    # (multiple-identity detection, cross-document checks) -- never
    # populated with real biometric data in this synthetic build.
    portrait_reference: str | None = None
    document_fingerprint: str | None = None
    created_at: dt.datetime
    issuer_signature: str = ""  # filled in by core/issuer/integrity.py


class IssuerRegistryProvider(Protocol):
    """Adapter seam: a future GovernmentIssuerRegistry / DigiLockerProvider
    / AuthorizedBorderDatabase implements this same shape; nothing else in
    the pipeline needs to change to swap it in."""

    def lookup(self, document_number: str) -> RegistryRecord | None: ...

    def verify_integrity(self) -> tuple[bool, dict]: ...

    def stats(self) -> dict[str, int]: ...