"""core/realdoc/crossdoc.py acceptance tests: cross-document field
comparison and re-fusion. Constructs ExtractedField directly -- no OCR
or image dependency, isolated from the rest of Mode B."""
from core.realdoc.crossdoc import add_crossdoc_evidence, build_crossdoc_step, compare_documents
from core.realdoc.fields import ExtractedField
from core.realdoc.risk import LadderStep, RealDocVerdict
from core.types import Severity, Tier


def _field(value: str, status: str = "EXTRACTED") -> ExtractedField:
    return ExtractedField(value=value, status=status, confidence="HIGH", source="test")


def test_matching_dob_is_consistent_and_zero_weight():
    fields_a = {"date_of_birth": _field("2004-08-14")}
    fields_b = {"date_of_birth": _field("2004-08-14")}
    signals = compare_documents(fields_a, fields_b)
    assert len(signals) == 1
    s = signals[0]
    assert s.severity == Severity.PASS
    assert s.weight == 0
    assert s.tier == Tier.RULES
    assert "consistent" in s.message.lower()


def test_conflicting_dob_fails_with_both_values_named():
    fields_a = {"date_of_birth": _field("2004-08-14")}
    fields_b = {"date_of_birth": _field("2001-01-24")}
    s = compare_documents(fields_a, fields_b)[0]
    assert s.severity == Severity.FAIL
    assert s.weight > 0
    assert "2004-08-14" in s.message and "2001-01-24" in s.message


def test_not_detected_on_either_side_is_weak_never_a_guess():
    fields_a = {"date_of_birth": _field("2004-08-14")}
    fields_b = {"date_of_birth": ExtractedField("", "NOT_DETECTED", "-", "")}
    s = compare_documents(fields_a, fields_b)[0]
    assert s.severity == Severity.WEAK
    assert s.weight == 0
    assert "not confidently read" in s.message.lower()


def test_uncertain_status_field_is_not_compared_as_confident():
    """UNCERTAIN (e.g. the positional name inference) must not be treated
    as a confident match/conflict, even when its value happens to agree --
    only EXTRACTED counts as a real read."""
    fields_a = {"date_of_birth": _field("2004-08-14", status="UNCERTAIN")}
    fields_b = {"date_of_birth": _field("2004-08-14")}
    s = compare_documents(fields_a, fields_b)[0]
    assert s.severity == Severity.WEAK
    assert s.weight == 0


def test_missing_field_key_entirely_is_treated_as_not_detected():
    fields_a = {}
    fields_b = {"date_of_birth": _field("2004-08-14")}
    s = compare_documents(fields_a, fields_b)[0]
    assert s.severity == Severity.WEAK


def test_build_crossdoc_step_prioritizes_fail_over_pass():
    from core.types import Signal
    signals = [
        Signal(tier=Tier.RULES, check="crossdoc_x", severity=Severity.PASS, weight=0, message="ok"),
        Signal(tier=Tier.RULES, check="crossdoc_y", severity=Severity.FAIL, weight=25, message="conflict"),
    ]
    step = build_crossdoc_step(signals)
    assert step.status == "FAILED"
    assert "conflict" in step.detail


def test_build_crossdoc_step_review_when_nothing_comparable():
    step = build_crossdoc_step([])
    assert step.status == "REVIEW"


def test_add_crossdoc_evidence_raises_score_on_conflict():
    base = RealDocVerdict(score=0, band="LOW", action="No action required",
                            steps=[LadderStep("Document Detection", "VERIFIED")], signals=[])
    fields_a = {"date_of_birth": _field("2004-08-14")}
    fields_b = {"date_of_birth": _field("2001-01-24")}
    cross_signals = compare_documents(fields_a, fields_b)
    updated = add_crossdoc_evidence(base, cross_signals)
    assert updated.score > 0
    assert updated.band != "LOW"
    assert any(s.name == "Cross-Document Consistency" for s in updated.steps)
    assert len(updated.steps) == len(base.steps) + 1


def test_add_crossdoc_evidence_never_reaches_critical():
    """Real-document mode's own invariant, preserved through re-fusion:
    no evidence combination here can ever produce CRITICAL."""
    base = RealDocVerdict(score=0, band="LOW", action="No action required", steps=[], signals=[])
    fields_a = {"date_of_birth": _field("2004-08-14")}
    fields_b = {"date_of_birth": _field("1901-01-01")}
    cross_signals = compare_documents(fields_a, fields_b)
    updated = add_crossdoc_evidence(base, cross_signals)
    assert updated.band != "CRITICAL"


def test_add_crossdoc_evidence_does_not_mutate_the_original_verdict():
    base = RealDocVerdict(score=0, band="LOW", action="No action required", steps=[], signals=[])
    fields_a = {"date_of_birth": _field("2004-08-14")}
    fields_b = {"date_of_birth": _field("2001-01-24")}
    cross_signals = compare_documents(fields_a, fields_b)
    add_crossdoc_evidence(base, cross_signals)
    assert base.score == 0
    assert base.band == "LOW"
    assert base.steps == []
