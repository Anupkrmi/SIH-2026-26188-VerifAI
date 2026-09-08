"""Curated, honestly-sourced explanations for why each check exists --
deliberately NOT a retrieval/RAG pipeline: no embeddings, no vector
store, nothing "retrieved" at runtime. A judge's "why is this required?"
deserves either a real, checkable source or an honest "this is our own
policy, not an external standard" -- never an invented citation.

Where the source is an external standard (ICAO Doc 9303), only claims
verifiable at the PART level are made here. This build does not assert
exact clause/section numbers, which would need a copy of the primary
document on hand to verify precisely -- claiming that precision without
it would be exactly the kind of fabricated citation this module exists
to avoid. Anything specific to how BorderShield itself works (weights,
thresholds, the synthetic registry) is cited to this repo's own files,
which are 100% checkable by construction.

The deterministic validators (core/rules/, core/issuer/, core/forensics/,
core/crypto/) remain solely responsible for actual validation -- nothing
here influences a verdict; this is explanation only.
"""
from __future__ import annotations

_ICAO = "ICAO Doc 9303 (Machine Readable Travel Documents)"

STANDARDS: dict[str, dict[str, str]] = {
    "mrz_checksum": {
        "rule": "Every MRZ field, and a composite over all of them, carries a check digit computed "
                "with a fixed weight-7/3/1 algorithm over a closed alphabet (A-Z, 0-9, '<'). A printed "
                "digit that doesn't match its field's recomputed value is a format failure, independent "
                "of whether the field's own content looks plausible.",
        "source": _ICAO + ", Part 3 (Specifications Common to All MRTDs)",
        "note": "Implemented in core/mrz.py, which documents the exact algorithm used.",
    },
    "crosszone": {
        "rule": "The visually-inspected zone (VIZ, the printed fields a human reads) and the "
                "machine-readable zone both encode the same identity data on a genuine document -- two "
                "independent encodings of the same claim, so they must agree.",
        "source": _ICAO + ", Part 3 (Specifications Common to All MRTDs)",
        "note": "Implemented in core/crosszone.py.",
    },
    "expiry_in_past": {
        "rule": "A travel document is not valid for its stated purpose once its own printed expiry "
                "date has passed.",
        "source": _ICAO + ", Part 3 (Specifications Common to All MRTDs)",
        "note": "Implemented in core/rules/engine.py; the weight is configurable in policy.yaml.",
    },
    "issue_after_expiry": {
        "rule": "A document's own issue date must precede its own expiry date -- a basic internal "
                "consistency check, not a claim about any external authority.",
        "source": "BorderShield Policy (internal consistency check)",
        "note": "core/rules/engine.py::_rule_issue_after_expiry.",
    },
    "dob_in_future": {
        "rule": "A date of birth printed after today's date is not internally consistent on any "
                "document, regardless of issuer.",
        "source": "BorderShield Policy (internal consistency check)",
        "note": "core/rules/engine.py::_rule_dob_in_future.",
    },
    "dob_implies_age_over_max": {
        "rule": "A date of birth implying an age beyond a configured plausible maximum (120 years by "
                "default) is a data-quality flag, not a claim about any external standard.",
        "source": "BorderShield Policy (plausibility check, threshold configurable in policy.yaml)",
        "note": "core/rules/engine.py::_rule_dob_implies_age_over_max.",
    },
    "signature_valid": {
        "rule": "The document's signed manifest must verify against the signature that was produced "
                "for it at intake; a mismatch means the record itself no longer matches what was "
                "attested.",
        "source": _ICAO + ", Part 11 (Security Mechanisms for MRTDs) -- Passive Authentication, general concept",
        "note": "core/crypto/manifest.py::verify_document.",
    },
    "signature_chain": {
        "rule": "The certificate that signed a document's manifest must itself chain back to the "
                "trusted signing authority's root -- a signature from an untrusted or unrelated key "
                "proves nothing.",
        "source": _ICAO + ", Part 12 (Public Key Infrastructure for MRTDs) -- general concept",
        "note": "core/crypto/pki.py::verify_chain.",
    },
    "document_number_format": {
        "rule": "Passport number format is an ISSUER convention, not an ICAO mandate -- ICAO leaves "
                "the number format itself to the issuing State. This build's synthetic issuer (UTO) "
                "always assigns 9 numeric digits; that specific pattern is BorderShield policy, not an "
                "ICAO rule.",
        "source": "BorderShield Policy",
        "note": "core/rules/policy.yaml -- document_number_format.pattern.",
    },
    "manifest_match": {
        "rule": "A signature over the document's captured data, verified against a trusted signing "
                "authority's certificate chain, proves the presented data is byte-identical to what was "
                "attested at intake. Loosely modelled on the Passive Authentication concept for eMRTDs, "
                "simplified here to two hashes (portrait + MRZ) rather than every chip data group.",
        "source": _ICAO + ", Part 11 (Security Mechanisms for MRTDs) -- Passive Authentication, general concept",
        "note": "core/crypto/manifest.py's own docstring states precisely what this does and does not prove.",
    },
    "photo_region_anomaly": {
        "rule": "Statistical properties of a genuine, single-source photograph (edge sharpness, "
                "boundary consistency) differ measurably from a pasted-in or recompressed region. A "
                "forensic heuristic, not a certified standard.",
        "source": "BorderShield Policy (forensic heuristic, advisory only)",
        "note": "core/forensics/photo_region.py.",
    },
    "recapture_anomaly": {
        "rule": "A photograph of a screen or a reprinted document tends to show moire patterns, "
                "compression artefacts, or glare that a direct capture of an original does not.",
        "source": "BorderShield Policy (forensic heuristic, advisory only)",
        "note": "core/forensics/recapture.py.",
    },
    "noise_residual_anomaly": {
        "rule": "A locally retouched region tends to leave a noise-texture residual that measurably "
                "differs from the surrounding untouched image.",
        "source": "BorderShield Policy (forensic heuristic, advisory only)",
        "note": "core/forensics/noise.py.",
    },
    "face_verification": {
        "rule": "1:1 biometric comparison of the document portrait against a live capture, behind a "
                "quality gate that refuses to score a capture too blurry or small to trust.",
        "source": "BorderShield Policy (SFace model, ONNX; threshold measured on this build's own test set)",
        "note": "core/face/pipeline.py; the measured threshold is in results/face_threshold.json.",
    },
    "issuer_status": {
        "rule": "A structurally valid, unexpired, correctly-signed document can still have been "
                "revoked, reported stolen, or otherwise invalidated by its issuing authority after "
                "printing. That is a fact about the CREDENTIAL's current standing, which no amount of "
                "document-level checking can determine on its own -- only a check against the issuer's "
                "own record can.",
        "source": "BorderShield Policy -- Synthetic Issuer Registry",
        "note": "core/issuer/ -- explicitly a demo/synthetic registry, never a real government system.",
    },
    "issuer_field_mismatch": {
        "rule": "A document number that exists in the registry only establishes that SOME document "
                "was issued under that number -- it does not establish that the person presenting it "
                "is who that record names. Name, date of birth and nationality are compared "
                "independently of the number lookup.",
        "source": "BorderShield Policy -- Synthetic Issuer Registry",
        "note": "core/issuer/compare.py.",
    },
    "issuer_lookup": {
        "rule": "A document number the registry has no record of at all is a different fact from a "
                "document the registry has flagged as invalid -- the honest answer is 'issuance could "
                "not be established', never 'fake'.",
        "source": "BorderShield Policy -- Synthetic Issuer Registry",
        "note": "core/issuer/compare.py.",
    },
    "identity_linkage": {
        "rule": "The same biometric identity is expected to map to exactly one active credential. More "
                "than one active credential sharing the same biometric reference is evidence worth a "
                "closer look -- not, by itself, proof that either credential is fraudulent.",
        "source": "BorderShield Policy -- Identity Continuity",
        "note": "core/issuer/linkage.py.",
    },
}


def lookup(check: str) -> dict[str, str] | None:
    """Longest-prefix match against STANDARDS' keys, so e.g.
    "mrz_checksum_date_of_birth" resolves via "mrz_checksum", and
    "issuer_status_revoked" resolves via "issuer_status". None if nothing
    is on file -- callers must render that as "not sourced yet", never
    guess one."""
    if check in STANDARDS:
        return STANDARDS[check]
    for key in sorted(STANDARDS, key=len, reverse=True):
        if check.startswith(key):
            return STANDARDS[key]
    return None