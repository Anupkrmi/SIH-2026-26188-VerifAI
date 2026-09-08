"""ui/actions.py export helpers: pure data-serialization functions, no
Streamlit runtime needed to test them directly."""
import datetime as dt
import json

from ui.actions import case_report_json, ledger_export_json


def test_case_report_json_round_trips_the_verdict():
    from core.crypto import ledger as ledger_module
    from core.mrz import MrzFields
    from core.types import Band, Severity, Signal, Tier, Verdict

    fields = MrzFields(issuing_state="UTO", surname="TEST", given_names="DEMO", passport_number="123456789",
                         nationality="UTO", date_of_birth=dt.date(1990, 1, 1), sex="M",
                         date_of_expiry=dt.date(2030, 1, 1))
    verdict = Verdict(score=0, band=Band.LOW, action="No action required",
                        signals=[Signal(tier=Tier.RULES, check="x", severity=Severity.PASS, weight=0, message="ok")])
    raw = case_report_json("abc123", "data/documents/demo_0001.png", verdict, fields)
    parsed = json.loads(raw)
    assert parsed["case_id"] == "abc123"
    assert parsed["document"] == "demo_0001.png"
    assert parsed["verdict"]["score"] == 0
    assert parsed["verdict"]["band"] == "LOW"
    assert parsed["extracted_identity"]["document_number"] == "123456789"
    assert len(parsed["signals"]) == 1
    assert parsed["signals"][0]["check"] == "x"
    del ledger_module  # imported only to confirm no accidental circular import


def test_ledger_export_json_carries_every_record_and_genesis_hash():
    from core.crypto import ledger
    records = [{"case_id": "a", "band": "LOW", "prev_hash": ledger.GENESIS_HASH, "this_hash": "abc"}]
    raw = ledger_export_json(records)
    parsed = json.loads(raw)
    assert parsed["genesis_hash"] == ledger.GENESIS_HASH
    assert parsed["records"] == records


def test_ledger_export_json_handles_empty_ledger():
    raw = ledger_export_json([])
    parsed = json.loads(raw)
    assert parsed["records"] == []
