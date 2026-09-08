"""Cross-document consistency: compares fields extracted from TWO
separately-screened real documents (e.g. a passport and a marksheet).
This is the actual mechanism behind "how do you verify a DOB without a
government database": if two independently-issued documents for the
same person both carry a date of birth, and it agrees, that is real
corroborating evidence -- no registry required. If it disagrees, that is
a real finding, worth exactly as much scrutiny as any other cross-field
mismatch this codebase already reports.

Deliberately opt-in and additive: core/realdoc/pipeline.py::screen_real_document
is unchanged and still screens exactly one document. This module composes
TWO of its independent results after the fact, reusing the same Signal/
Severity/Tier vocabulary and the same core/realdoc/risk.py::fuse_realdoc
re-fusion, rather than threading a second document through the tested
single-document path.
"""
from __future__ import annotations

from core.realdoc.fields import ExtractedField
from core.realdoc.risk import LadderStep, RealDocVerdict, fuse_realdoc
from core.rules.engine import load_policy
from core.types import Severity, Signal, Tier

# Fields worth comparing across two arbitrary, differently-typed documents.
# name/nationality are free text and vary too much in OCR noise/casing/
# formatting to compare usefully without a real fuzzy-match model this
# build doesn't have; date_of_birth is the field two unrelated document
# TYPES (passport vs marksheet vs ID) are most likely to BOTH carry, and
# it's the actual field this feature exists to answer for.
_COMPARABLE = ("date_of_birth",)


def compare_documents(fields_a: dict[str, ExtractedField], fields_b: dict[str, ExtractedField],
                       policy: dict | None = None) -> list[Signal]:
    """One Signal per comparable field -- WEAK (zero weight) when either
    side didn't confidently read it, never a guess at a field neither, or
    only one, document actually produced."""
    policy = policy or load_policy()
    weight = int(policy["risk_weights"]["cross_field_mismatch"])
    signals: list[Signal] = []
    for key in _COMPARABLE:
        a, b = fields_a.get(key), fields_b.get(key)
        label = key.replace("_", " ").title()
        # EXTRACTED only -- UNCERTAIN (e.g. positional inference) is not a
        # confident enough read to call a cross-document MATCH or CONFLICT
        # on, even if its value happens to line up.
        a_ok = a is not None and a.status == "EXTRACTED" and bool(a.value)
        b_ok = b is not None and b.status == "EXTRACTED" and bool(b.value)
        detail = {"field": key, "document_a": a.value if a else "", "document_b": b.value if b else ""}

        if not (a_ok and b_ok):
            signals.append(Signal(
                tier=Tier.RULES, check=f"crossdoc_{key}", severity=Severity.WEAK, weight=0,
                message=f"{label} could not be compared -- not confidently read on both documents",
                detail=detail,
            ))
        elif a.value == b.value:
            signals.append(Signal(
                tier=Tier.RULES, check=f"crossdoc_{key}", severity=Severity.PASS, weight=0,
                message=f"{label} is consistent across both documents ({a.value})",
                detail=detail,
            ))
        else:
            signals.append(Signal(
                tier=Tier.RULES, check=f"crossdoc_{key}", severity=Severity.FAIL, weight=weight,
                message=f"{label} conflicts across documents: {a.value} vs {b.value}",
                detail=detail,
            ))
    return signals


def build_crossdoc_step(cross_signals: list[Signal]) -> LadderStep:
    fails = [s for s in cross_signals if s.severity == Severity.FAIL]
    passes = [s for s in cross_signals if s.severity == Severity.PASS]
    if fails:
        return LadderStep("Cross-Document Consistency", "FAILED", "; ".join(s.message for s in fails))
    if passes:
        return LadderStep("Cross-Document Consistency", "VERIFIED", "; ".join(s.message for s in passes))
    return LadderStep("Cross-Document Consistency", "REVIEW",
                       "No comparable fields were confidently read on both documents")


def add_crossdoc_evidence(verdict: RealDocVerdict, cross_signals: list[Signal],
                           policy: dict | None = None) -> RealDocVerdict:
    """Re-fuses an already-screened document's verdict with cross-document
    comparison evidence against a second, separately screened document.
    Returns a NEW verdict -- never mutates the one passed in, matching
    fuse_realdoc's own contract. Preserves an original REVIEW-for-
    insufficient-evidence state rather than silently overriding it."""
    policy = policy or load_policy()
    step = build_crossdoc_step(cross_signals)
    return fuse_realdoc(verdict.signals + cross_signals, verdict.steps + [step],
                         insufficient_evidence=(verdict.band == "REVIEW"), policy=policy)