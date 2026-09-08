"""Compares a screened document's MRZ-decoded fields against its Issuer
Registry record and produces the Tier.ISSUER Signal core/risk.py fuses.

Deliberately conservative in wording: NOT_FOUND never reads as "fake" --
it reads as "issuance could not be established", a different and weaker
claim. See core/issuer/registry.py for what NOT_FOUND actually means (no
matching row, not a bad row).
"""
from __future__ import annotations

from core.issuer.models import RegistryRecord, RegistryStatus
from core.mrz import MrzFields
from core.types import Severity, Signal, Tier


def _weight(policy: dict, key: str) -> int:
    return int(policy["risk_weights"][key])


def _compare_fields(fields: MrzFields, record: RegistryRecord) -> dict[str, bool]:
    presented_name = f"{fields.surname} {fields.given_names}".strip().upper()
    return {
        "document_number": fields.passport_number == record.document_number,
        "name": presented_name == record.name.strip().upper(),
        "date_of_birth": fields.date_of_birth == record.date_of_birth,
        "nationality": fields.nationality == record.nationality,
    }


def compare_to_document(fields: MrzFields, record: RegistryRecord | None, policy: dict) -> Signal:
    if record is None:
        return Signal(
            tier=Tier.ISSUER, check="issuer_lookup", severity=Severity.WEAK, weight=0,
            message="Issuance could not be established from the configured registry.",
            detail={"status": "NOT_FOUND", "document_number": fields.passport_number},
        )

    field_checks = _compare_fields(fields, record)
    mismatched = [name for name, ok in field_checks.items() if not ok]
    reason = record.revocation_reason or "reason not recorded"

    if record.status == RegistryStatus.REVOKED:
        return Signal(
            tier=Tier.ISSUER, check="issuer_status_revoked", severity=Severity.FAIL,
            weight=_weight(policy, "issuer_revoked"),
            message=f"Registry record for this document is REVOKED ({reason})",
            detail={"status": "REVOKED", "revocation_reason": record.revocation_reason,
                    "fields": field_checks},
        )
    if record.status == RegistryStatus.STOLEN:
        return Signal(
            tier=Tier.ISSUER, check="issuer_status_stolen", severity=Severity.FAIL,
            weight=_weight(policy, "issuer_stolen"),
            message=f"Registry record for this document is marked STOLEN ({reason})",
            detail={"status": "STOLEN", "revocation_reason": record.revocation_reason,
                    "fields": field_checks},
        )
    if record.status == RegistryStatus.INVALID:
        return Signal(
            tier=Tier.ISSUER, check="issuer_status_invalid", severity=Severity.FAIL,
            weight=_weight(policy, "issuer_revoked"),
            message="Registry record for this document is marked INVALID",
            detail={"status": "INVALID", "fields": field_checks},
        )
    if record.status == RegistryStatus.EXPIRED:
        return Signal(
            tier=Tier.ISSUER, check="issuer_status_expired", severity=Severity.FAIL,
            weight=_weight(policy, "expired_document"),
            message=f"Registry record for this document expired on {record.expiry_date}",
            detail={"status": "EXPIRED", "fields": field_checks},
        )

    # ACTIVE from here.
    if mismatched:
        return Signal(
            tier=Tier.ISSUER, check="issuer_field_mismatch", severity=Severity.FAIL,
            weight=_weight(policy, "issuer_mismatch"),
            message=f"Issuer registry record disagrees with the presented document on: {', '.join(mismatched)}",
            detail={"status": "ACTIVE", "fields": field_checks},
        )
    return Signal(
        tier=Tier.ISSUER, check="issuer_lookup", severity=Severity.PASS, weight=0,
        message="Document data matches the issuer registry record (status ACTIVE)",
        detail={"status": "ACTIVE", "fields": field_checks},
    )