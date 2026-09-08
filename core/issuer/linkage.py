"""Multiple-identity detection (spec Feature 4): does this credential's
biometric reference also appear on a DIFFERENT registry record?

Deliberately a registry cross-reference, not a face-similarity computation
-- portrait_reference is a synthetic symbolic cluster label (see
core/issuer/models.py), never a real embedding, so there is no similarity
score to report and none is fabricated. Wording stays at "possible
linkage detected", never a certainty claim -- see core/risk.py's
_DECISIVE_TIERS, which Tier.IDENTITY is deliberately NOT a member of:
this can raise a case for review, it can never condemn one alone.
"""
from __future__ import annotations

from core.issuer.models import RegistryRecord
from core.issuer.registry import SyntheticIssuerRegistry
from core.types import Severity, Signal, Tier


def _weight(policy: dict, key: str) -> int:
    return int(policy["risk_weights"][key])


def check_identity_linkage(record: RegistryRecord | None, registry: SyntheticIssuerRegistry,
                            policy: dict) -> Signal | None:
    """None if there's no registry record to check linkage against at all
    (NOT_FOUND) -- Tier.IDENTITY then renders N/A on the ladder, the same
    way Tier.BIOMETRIC does when there's no portrait to compare."""
    if record is None:
        return None

    linked = registry.find_linked_records(record.portrait_reference, record.registry_record_id)
    if not linked:
        return Signal(
            tier=Tier.IDENTITY, check="identity_linkage", severity=Severity.PASS, weight=0,
            message="No other registry record shares this credential's biometric reference",
            detail={"linked": []},
        )

    linked_info = [
        {"registry_record_id": r.registry_record_id, "person_id": r.person_id,
         "document_number": r.document_number, "name": r.name}
        for r in linked
    ]
    names = ", ".join(f"{i['name']} ({i['document_number']})" for i in linked_info)
    return Signal(
        tier=Tier.IDENTITY, check="identity_linkage", severity=Severity.FAIL,
        weight=_weight(policy, "identity_linkage"),
        message=f"Possible identity linkage detected: also associated with {names}",
        detail={"linked": linked_info},
    )