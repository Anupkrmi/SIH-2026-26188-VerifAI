"""core/mrz.py acceptance test, per the plan: build a valid MRZ, mutate one
character at every checksum-protected position in turn, assert every
mutation is caught.

Scope note, and it is a real property of the ICAO spec, not a gap in this
test: TD3's name field (line 1) and the nationality sub-field (line 2)
carry NO check digit at all -- only passport number, date of birth, date
of expiry, personal number, and the composite digit are checksum-protected.
Mutations are therefore exercised over exactly the protected span.

The fixture uses an all-digit passport number and an empty (all '<')
personal number so every checksum-protected character is either a digit
or '<'. That sidesteps the scheme's real, intrinsic blind spot (see the
comment above check_digit in core/mrz.py): a value delta that is an exact
multiple of 10 is invisible to every check digit including the composite.
Testing across digits/'<' only never trips that blind spot by accident.
"""
import datetime as dt

import pytest

from core.mrz import (
    MrzFields, build_td3, check_digit, correct_with_checkdigits,
    decode_fields, validate_checkdigits,
)


def _fixture() -> MrzFields:
    return MrzFields(
        issuing_state="UTO",
        surname="SINGH PALL",
        given_names="RAJVEER",
        passport_number="123456789",   # all-digit: avoids the mod-10 blind spot
        nationality="UTO",
        date_of_birth=dt.date(1998, 8, 14),
        sex="M",
        date_of_expiry=dt.date(2032, 8, 13),
        personal_number="",             # all '<': same reason
    )


def test_build_produces_correct_lengths():
    line1, line2 = build_td3(_fixture())
    assert len(line1) == 44
    assert len(line2) == 44


def test_valid_mrz_passes_every_check_digit():
    line1, line2 = build_td3(_fixture())
    checks = validate_checkdigits(line2)
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]


def test_build_parse_roundtrip():
    fields = _fixture()
    line1, line2 = build_td3(fields)
    decoded = decode_fields(line1, line2)
    assert decoded.issuing_state == fields.issuing_state
    assert decoded.surname == fields.surname
    assert decoded.given_names == fields.given_names
    assert decoded.passport_number == fields.passport_number
    assert decoded.nationality == fields.nationality
    assert decoded.date_of_birth == fields.date_of_birth
    assert decoded.sex == fields.sex
    assert decoded.date_of_expiry == fields.date_of_expiry


def _mutate_digit(c: str) -> str:
    """Cyclic +1 for a digit, or '<' -> '1'. Delta is always in {1..9},
    never a multiple of 10 -- guaranteed detectable, see module docstring."""
    if c == "<":
        return "1"
    return str((int(c) + 1) % 10)


# Every position covered by a check digit: passport number + its digit,
# DOB + its digit, expiry + its digit, personal number + its digit, and
# the composite digit itself.
_PROTECTED_SPANS = [(0, 10), (13, 20), (21, 28), (28, 43)]


@pytest.mark.parametrize("position", [
    p for start, end in _PROTECTED_SPANS for p in range(start, end)
] + [43])
def test_every_protected_position_mutation_is_caught(position):
    _, line2 = build_td3(_fixture())
    original_char = line2[position]
    mutated_char = _mutate_digit(original_char)
    assert mutated_char != original_char

    mutated_line2 = line2[:position] + mutated_char + line2[position + 1:]
    checks = validate_checkdigits(mutated_line2)
    assert any(not c.ok for c in checks), (
        f"mutation at position {position} ({original_char!r}->{mutated_char!r}) "
        f"was not caught by any check digit"
    )


def test_checksum_guided_correction_recovers_single_ocr_error():
    _, line2 = build_td3(_fixture())
    # simulate a realistic OCR confusion: a printed '1' misread as letter 'I',
    # inside the passport number ("123456789" -> field position 0 is '1').
    pos = 0
    assert line2[pos] == "1", "fixture assumption changed; update pos"
    corrupted = line2[:pos] + "I" + line2[pos + 1:]  # 'I' is a valid MRZ char
    # give it low confidence at the corrupted cell so correction tries it first
    confidences = [0.99] * 44
    confidences[pos] = 0.10
    corrected, notes = correct_with_checkdigits(corrupted, confidences)
    assert notes, "expected at least one correction note"
    assert corrected == line2, "should recover exactly the original MRZ line"
    checks = validate_checkdigits(corrected)
    assert all(c.ok for c in checks), "corrected MRZ should pass every check digit"


def test_checksum_guided_correction_reports_uncorrectable_errors_honestly():
    """A corruption that is NOT a member of the confusion set (e.g. a
    completely wrong digit) has no single-substitution fix available, and
    the function must say so rather than silently returning something
    wrong or crashing."""
    _, line2 = build_td3(_fixture())
    pos = 2  # passport_number field position 2 is '3' in the fixture
    assert line2[pos] == "3"
    corrupted = line2[:pos] + "8" + line2[pos + 1:]  # not a confusable pair with '3'
    confidences = [0.99] * 44
    confidences[pos] = 0.10
    corrected, notes = correct_with_checkdigits(corrupted, confidences)
    assert any("no single-character correction found" in n for n in notes)


def test_check_digit_known_algorithm_examples():
    # value mapping + weights, worked by hand: "7" -> value 7, single char,
    # weight 7 (first position) -> 7*7=49 -> mod10 = 9
    assert check_digit("7") == "9"
    # "<" always contributes 0 regardless of position/weight
    assert check_digit("<<<") == "0"
