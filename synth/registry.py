"""Generates the Synthetic / Demonstration Issuer Registry
(data/registry/registry.db): a SQLite stand-in for what an authorized
issuer connector would provide, NOT a connection to any real government
database. Run after synth.passport (record REG-0001 below is read
straight from the genuine demo document's own ground-truth JSON, so a
genuine screening always finds a matching ACTIVE record).

Every one of the 16 columns core/issuer/models.py::RegistryRecord defines
is filled for every row -- with two deliberate exceptions that are
honest NULLs, not gaps: `revocation_reason` only means something for a
REVOKED/STOLEN/INVALID record (filling it for an ACTIVE one would be a
fabricated value), and `document_fingerprint` can only be a REAL hash for
REG-0001, the one record with an actual generated document image (see
_document_fingerprint below).

`portrait_reference` is a synthetic face-cluster label
(PORTRAIT-CLUSTER-NN), never a real photo, embedding, or file path --
matches the project's own privacy stance (no unnecessary biometric
storage). Two records sharing the SAME cluster label is the seed for
Feature 4 (multiple-identity detection): REG-0006 and REG-0007 below are
two different people/documents/credentials pointing at one cluster,
i.e. "this face has been issued two separate identities" -- the actual
comparison/detection logic is a separate, not-yet-built feature; this
file only makes the data support it.

`document_type` is deliberately varied (PASSPORT / NATIONAL_ID /
DRIVING_LICENCE / EDUCATIONAL_CERTIFICATE) ahead of the cross-document
validation feature, which needs more than one document class to compare
across.

Demo attack this sets up (not yet wired to a UI button -- see
core/issuer/registry.py::verify_integrity and tests/test_issuer.py):
hand-edit REG-0002's stored `status` from REVOKED to ACTIVE directly in
the SQLite file without recomputing its `issuer_signature` fingerprint.
verify_integrity() then reports the record's fingerprint no longer
matches what's stored -- "registry integrity compromised" -- without
needing to know what changed inside it.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from config import PATHS
from core.issuer.integrity import record_fingerprint
from core.issuer.models import RegistryRecord, RegistryStatus
from core.issuer.registry import get_default_registry, init_db, insert_record

_ISSUER_ID = "UTO-DEMO-AUTH"
_CREATED_AT = dt.datetime(2026, 8, 30, tzinfo=dt.timezone.utc)


def _document_fingerprint_real(image_path: Path) -> str:
    """sha256 of the ACTUAL generated document image bytes -- only
    possible for a record that has a real document behind it."""
    return hashlib.sha256(image_path.read_bytes()).hexdigest()


def _document_fingerprint_placeholder(document_number: str) -> str:
    """Deterministic filler for a record with no generated document image
    to hash. Namespaced with a literal "synthetic-placeholder:" prefix so
    it can never be read as, or mistaken for, a real image hash -- a real
    deployment would replace this with sha256(actual document bytes) at
    intake, same as _document_fingerprint_real does for REG-0001."""
    payload = f"synthetic-placeholder:{_ISSUER_ID}:{document_number}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _genuine_record() -> RegistryRecord:
    """REG-0001: the actual generated demo passport's own fields, read from
    its ground-truth JSON -- never recomputed independently, so this can
    never drift from what synth/passport.py actually drew on the document
    (and, downstream, what core/mrz.py's decode_fields() actually reads
    off it). The only record with a REAL document_fingerprint, because
    it's the only one with a real generated image to hash."""
    truth_path = PATHS["documents"] / "demo_0001.json"
    truth = json.loads(truth_path.read_text())
    f = truth["fields"]
    raw = truth["raw_dates"]
    doc_number = f["passport_number"]
    return RegistryRecord(
        registry_record_id="REG-0001",
        document_number=doc_number,
        document_type="PASSPORT",
        issuer_id=_ISSUER_ID,
        person_id="P001",
        name=f"{f['surname']} {f['given_names']}".strip().upper(),
        date_of_birth=dt.date.fromisoformat(raw["date_of_birth"]),
        nationality=f["nationality"],
        issue_date=dt.date.fromisoformat(raw["date_of_issue"]),
        expiry_date=dt.date.fromisoformat(raw["date_of_expiry"]),
        status=RegistryStatus.ACTIVE,
        portrait_reference="PORTRAIT-CLUSTER-01",
        document_fingerprint=_document_fingerprint_real(PATHS["documents"] / "demo_0001.png"),
        created_at=_CREATED_AT,
    )


# (registry_record_id, document_number, document_type, person_id, name,
#  date_of_birth, nationality, issue_date, expiry_date, status,
#  revocation_reason, portrait_cluster)
_SYNTHETIC_ROWS = [
    ("REG-0002", "900000002", "PASSPORT", "P002", "KHAN SAMEER",
     dt.date(1998, 5, 12), "UTO", dt.date(2015, 1, 1), dt.date(2032, 1, 1),
     RegistryStatus.REVOKED, "Reported lost; reissued under a new document number",
     "PORTRAIT-CLUSTER-02"),
    ("REG-0003", "900000003", "PASSPORT", "P003", "NAIR PRIYA",
     dt.date(1995, 11, 3), "UTO", dt.date(2018, 6, 1), dt.date(2028, 6, 1),
     RegistryStatus.STOLEN, "Reported stolen by holder",
     "PORTRAIT-CLUSTER-03"),
    ("REG-0004", "900000004", "PASSPORT", "P004", "DESAI VIKRAM",
     dt.date(1990, 7, 20), "UTO", dt.date(2010, 1, 15), dt.date(2020, 1, 15),
     RegistryStatus.EXPIRED, None,
     "PORTRAIT-CLUSTER-04"),
    ("REG-0005", "900000005", "PASSPORT", "P005", "RAI NEHA",
     dt.date(2000, 3, 9), "UTO", dt.date(2023, 6, 1), dt.date(2033, 6, 1),
     RegistryStatus.ACTIVE, None,
     "PORTRAIT-CLUSTER-05"),
    # -- Multiple-identity seed pair: different person_id, different
    # document_number, different name/DOB, SAME portrait cluster. This is
    # the "one face, two credentials" scenario Feature 4 needs data for.
    ("REG-0006", "900000006", "PASSPORT", "P006", "MEHTA ARJUN",
     dt.date(1993, 9, 14), "UTO", dt.date(2021, 3, 1), dt.date(2031, 3, 1),
     RegistryStatus.ACTIVE, None,
     "PORTRAIT-CLUSTER-07"),
    ("REG-0007", "900000007", "PASSPORT", "P007", "BHATT ROHAN",
     dt.date(1991, 2, 27), "UTO", dt.date(2022, 7, 10), dt.date(2032, 7, 10),
     RegistryStatus.ACTIVE, None,
     "PORTRAIT-CLUSTER-07"),
    # -- Document-type variety, ahead of cross-document validation.
    ("REG-0008", "900000008", "NATIONAL_ID", "P008", "IYER KAVYA",
     dt.date(1988, 12, 5), "UTO", dt.date(2019, 1, 1), dt.date(2029, 1, 1),
     RegistryStatus.ACTIVE, None,
     "PORTRAIT-CLUSTER-08"),
    ("REG-0009", "900000009", "DRIVING_LICENCE", "P009", "CHATTERJEE ADITYA",
     dt.date(1996, 4, 18), "UTO", dt.date(2020, 9, 1), dt.date(2030, 9, 1),
     RegistryStatus.ACTIVE, None,
     "PORTRAIT-CLUSTER-09"),
    ("REG-0010", "900000010", "EDUCATIONAL_CERTIFICATE", "P010", "BOSE ISHAAN",
     dt.date(2002, 8, 22), "UTO", dt.date(2023, 5, 15), dt.date(2033, 5, 15),
     RegistryStatus.ACTIVE, None,
     "PORTRAIT-CLUSTER-10"),
    # -- INVALID: the one status value the first pass never seeded.
    ("REG-0011", "900000011", "PASSPORT", "P011", "JOSHI MEERA",
     dt.date(1999, 11, 30), "UTO", dt.date(2024, 2, 1), dt.date(2034, 2, 1),
     RegistryStatus.INVALID, "Failed issuer validation at printing (specimen record)",
     "PORTRAIT-CLUSTER-11"),
    ("REG-0012", "900000012", "PASSPORT", "P012", "KAPOOR SIDDHARTH",
     dt.date(1985, 3, 8), "UTO", dt.date(2016, 6, 1), dt.date(2026, 6, 1),
     RegistryStatus.REVOKED, "Superseded by reissued document after a name correction",
     "PORTRAIT-CLUSTER-12"),
]


def _synthetic_records() -> list[RegistryRecord]:
    return [
        RegistryRecord(
            registry_record_id=row_id, document_number=doc_no, document_type=doc_type,
            issuer_id=_ISSUER_ID, person_id=person_id, name=name,
            date_of_birth=dob, nationality=nationality, issue_date=issue, expiry_date=expiry,
            status=status, revocation_reason=reason, portrait_reference=cluster,
            document_fingerprint=_document_fingerprint_placeholder(doc_no),
            created_at=_CREATED_AT,
        )
        for (row_id, doc_no, doc_type, person_id, name, dob, nationality, issue, expiry,
             status, reason, cluster) in _SYNTHETIC_ROWS
    ]


def generate() -> None:
    PATHS["registry"].mkdir(parents=True, exist_ok=True)
    db_path = PATHS["registry_db"]
    init_db(db_path)

    records = [_genuine_record(), *_synthetic_records()]
    for record in records:
        record.issuer_signature = record_fingerprint(record)
        insert_record(db_path, record)

    print(f"wrote {db_path} ({len(records)} records)")
    for r in records:
        print(f"  {r.registry_record_id}  {r.document_number}  {r.document_type:24s}  "
              f"{r.status.value:8s}  {r.portrait_reference:20s}  {r.name}")

    clusters: dict[str, list[str]] = {}
    for r in records:
        clusters.setdefault(r.portrait_reference, []).append(r.registry_record_id)
    linked = {k: v for k, v in clusters.items() if len(v) > 1}
    print(f"shared portrait clusters (multi-identity seed): {linked}")

    # Sign the manifest now too, so a freshly generated registry is already
    # integrity-valid on THIS machine without waiting for the app's first
    # Command Center render -- purely a convenience for local dev/demo prep,
    # not required (get_default_registry().ensure_signed() is called lazily
    # wherever registry status is actually displayed).
    get_default_registry.cache_clear()
    ok, detail = get_default_registry().verify_integrity()
    print(f"registry integrity: {'VALID' if ok else 'COMPROMISED'} -- {detail}")


if __name__ == "__main__":
    generate()
