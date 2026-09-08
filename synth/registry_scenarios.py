"""Generates the extra synthetic documents the Issuer-Registry Attack Wall
scenarios need: self-consistent, cleanly-signed documents whose ONLY
problem is what the registry says about them -- not a pixel-level forgery
like synth/forge.py's attacks. This is the demo BorderShield AI's Issuer
Registry actually exists for: "the document looks perfect" and "the
document is trustworthy" are different claims, and forensics/crypto/MRZ
checks can only ever answer the first one.

Run after synth.passport and synth.registry -- REVOKED_FIELDS mirrors
synth/registry.py's REG-0002 exactly (same person, same document),
MISMATCH_FIELDS deliberately presents REG-0001's real ACTIVE document
number under a different identity than the one actually registered to
it, LINKED_FIELDS mirrors REG-0006 (clean on its own, but sharing a
portrait cluster with REG-0007), STOLEN_FIELDS mirrors REG-0003,
UNREGISTERED_FIELDS uses a document number that exists in NO registry
record at all, and EXPIRED_FIELDS mirrors REG-0004's identity but with
the document's OWN printed dates left current -- the physical document
looks freshly issued; only the registry's older record for that number
says EXPIRED. All render through the same generic generator demo_0001
does, so MRZ, VIZ, crosszone and (once signed) crypto all agree with
EACH OTHER and pass cleanly -- only core/issuer/compare.py's registry
lookup or core/issuer/linkage.py's cross-reference catches any of them.
"""
from __future__ import annotations

import datetime as dt

from config import SEED
from synth.passport import DocumentFields, generate

REVOKED_FIELDS = DocumentFields(
    issuing_state="UTO", surname="KHAN", given_names="SAMEER",
    passport_number="900000002", nationality="UTO",
    date_of_birth=dt.date(1998, 5, 12), sex="M",
    date_of_issue=dt.date(2015, 1, 1), date_of_expiry=dt.date(2032, 1, 1),
    personal_number="",
)

MISMATCH_FIELDS = DocumentFields(
    issuing_state="UTO", surname="PATEL", given_names="RAVI",
    passport_number="181960013", nationality="UTO",
    date_of_birth=dt.date(1985, 3, 15), sex="M",
    date_of_issue=dt.date(2024, 5, 8), date_of_expiry=dt.date(2034, 5, 8),
    personal_number="",
)

# Mirrors REG-0006 (Mehta Arjun) exactly -- REG-0006 and REG-0007 (Bhatt
# Rohan) share PORTRAIT-CLUSTER-07 in the seed data. This document's own
# registry record is perfectly clean (ACTIVE, every field matches); only
# core/issuer/linkage.py's cross-reference finds the second credential
# pointing at the same biometric cluster.
LINKED_FIELDS = DocumentFields(
    issuing_state="UTO", surname="MEHTA", given_names="ARJUN",
    passport_number="900000006", nationality="UTO",
    date_of_birth=dt.date(1993, 9, 14), sex="M",
    date_of_issue=dt.date(2021, 3, 1), date_of_expiry=dt.date(2031, 3, 1),
    personal_number="",
)

# Mirrors REG-0003 (Nair Priya) exactly.
STOLEN_FIELDS = DocumentFields(
    issuing_state="UTO", surname="NAIR", given_names="PRIYA",
    passport_number="900000003", nationality="UTO",
    date_of_birth=dt.date(1995, 11, 3), sex="F",
    date_of_issue=dt.date(2018, 6, 1), date_of_expiry=dt.date(2028, 6, 1),
    personal_number="",
)

# A document number that appears in NO registry record at all -- the
# honest "issuance could not be established" case, never reported as fake.
UNREGISTERED_FIELDS = DocumentFields(
    issuing_state="UTO", surname="GILL", given_names="SIMRAN",
    passport_number="900000099", nationality="UTO",
    date_of_birth=dt.date(1997, 8, 2), sex="F",
    date_of_issue=dt.date(2022, 4, 1), date_of_expiry=dt.date(2032, 4, 1),
    personal_number="",
)

# Same identity as REG-0004 (Desai Vikram, whose REGISTRY expiry_date is
# 2020-01-15 -- already in the past) but the document's OWN printed
# issue/expiry are left current. Name/DOB/nationality still match the
# registry record exactly, so this isolates the EXPIRED registry status
# as the only signal -- distinct from the document's own expiry_in_past
# rule, which this document satisfies cleanly on its own.
EXPIRED_FIELDS = DocumentFields(
    issuing_state="UTO", surname="DESAI", given_names="VIKRAM",
    passport_number="900000004", nationality="UTO",
    date_of_birth=dt.date(1990, 7, 20), sex="M",
    date_of_issue=dt.date(2024, 1, 1), date_of_expiry=dt.date(2034, 1, 1),
    personal_number="",
)

# Mirrors REG-0011 (Joshi Meera) -- INVALID is the one registry status
# value the Attack Wall hadn't demonstrated yet (distinct from REVOKED:
# never validly issued/standing to begin with, rather than issued then
# later invalidated).
INVALID_FIELDS = DocumentFields(
    issuing_state="UTO", surname="JOSHI", given_names="MEERA",
    passport_number="900000011", nationality="UTO",
    date_of_birth=dt.date(1999, 11, 30), sex="F",
    date_of_issue=dt.date(2024, 2, 1), date_of_expiry=dt.date(2034, 2, 1),
    personal_number="",
)

REVOKED_DOC_ID = "demo_revoked_0002"
MISMATCH_DOC_ID = "demo_mismatch_0001"
LINKED_DOC_ID = "demo_linked_0006"
STOLEN_DOC_ID = "demo_stolen_0003"
UNREGISTERED_DOC_ID = "demo_unregistered_0099"
EXPIRED_DOC_ID = "demo_expired_0004"
INVALID_DOC_ID = "demo_invalid_0011"


def generate_scenarios() -> None:
    scenarios = (
        (REVOKED_DOC_ID, REVOKED_FIELDS),
        (MISMATCH_DOC_ID, MISMATCH_FIELDS),
        (LINKED_DOC_ID, LINKED_FIELDS),
        (STOLEN_DOC_ID, STOLEN_FIELDS),
        (UNREGISTERED_DOC_ID, UNREGISTERED_FIELDS),
        (EXPIRED_DOC_ID, EXPIRED_FIELDS),
        (INVALID_DOC_ID, INVALID_FIELDS),
    )
    for doc_id, fields in scenarios:
        png_path, json_path = generate(doc_id, fields=fields, seed=SEED)
        print(f"wrote {png_path}")
        print(f"wrote {json_path}")

    from synth.sign import sign_all
    sign_all()


if __name__ == "__main__":
    generate_scenarios()
