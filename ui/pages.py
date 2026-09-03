"""The 5 screens of the console, one function each. These orchestrate:
they call ui/screens.py for markup and ui/actions.py for logic, and they
freely touch st.session_state/widgets themselves -- a different, wider
contract than ui/screens.py's pure-render one. app.py just dispatches to
whichever of these the sidebar nav selected.

Real Streamlit widgets (buttons, uploaders, images) are never nested
inside raw HTML injected via a separate st.markdown call -- an unclosed
`<div>` from one st.markdown does not actually wrap a later, sibling
st.button in the rendered DOM, it only looks that way in the source. Any
box that needs a widget inside it uses st.container(border=True) instead,
which really does parent its children.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import streamlit as st
from PIL import Image

from config import DOC_SIZE, PATHS
from core.crypto import ledger as ledger_module
from core.face.pipeline import verify as face_verify
from core.fields import PORTRAIT_BBOX
from core.forensics.heatmap import overlay
from core.realdoc import loader
from core.realdoc.pipeline import screen_real_document
from core.risk import traffic_light
from core.rules.engine import load_policy
from core.types import Severity
from ui import actions, screens

_LIGHT_CLASS = {"GREEN": "green", "AMBER": "amber", "RED": "red"}


def render_landing() -> None:
    """The front page: what this project is, before any live data.

    Deliberately the app's default screen. Opening straight into the
    operating console gave a first-time viewer (a judge, a reviewer) no
    way to learn the thesis before being shown a table of case IDs. This
    page is read once; every other screen is operated repeatedly.
    """
    st.markdown(screens.hero_html(), unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='bsx-tier-head'>The trust ladder</div>", unsafe_allow_html=True)
        st.caption("Four tiers, evaluated in this order. A tier's authority is fixed by the "
                    "architecture, not by how confident a model happens to be.")
        st.write("")
        st.markdown(screens.trust_ladder_html(), unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown("<div class='bsx-tier-head'>Start here</div>", unsafe_allow_html=True)
        st.caption("Six controlled attack vectors are wired to the real pipeline. Each one forges a "
                    "document, screens it end to end, and writes a hash-chained case.")
        st.write("")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Open screening command", type="primary", use_container_width=True,
                          icon=":material/dashboard:", key="landing_to_dash"):
                st.session_state.page = "dashboard"
                st.rerun()
        with c2:
            if st.button("Screen a document", use_container_width=True,
                          icon=":material/person_search:", key="landing_to_capture"):
                st.session_state.page = "capture"
                st.rerun()

    st.write("")
    with st.container():
        st.markdown("<div class='bsx-tier-head'>What this is not</div>", unsafe_allow_html=True)
        st.write("")
        st.markdown(screens.honesty_html(), unsafe_allow_html=True)


def render_dashboard() -> None:
    chain_ok, broken_at = ledger_module.verify_chain()
    records = ledger_module.read_all()

    st.markdown(screens.topbar_html(
        "Screening command",
        # Precise about WHICH half is real. "Nothing here is staged" was
        # true of the processing and false of the documents, and a judge
        # is entitled to read it the stricter way.
        "Every scenario runs through the same live verification pipeline the app uses for any "
        "document. The test documents themselves are synthetic and deliberately controlled.",
        eyebrow="PS 26188 · Ministry of Home Affairs · Sashastra Seema Bal",
        chain_ok=chain_ok), unsafe_allow_html=True)

    # Four real status cards -- each backed by an actual file check or
    # ledger read, never a fabricated "engine version" or confidence
    # number. See PLAN_redesign.md's substitution map for the mockup
    # panels these replace.
    models = actions.models_status()
    face_ready = all(m["exists"] for m in models if "Face" in m["label"])
    critical = sum(1 for r in records if r.get("band") == "CRITICAL")
    high_review = sum(1 for r in records if r.get("band") in ("HIGH", "CRITICAL"))
    st.markdown(screens.status_grid_html([
        screens.status_card_html(
            "Biometric models", "READY" if face_ready else "MISSING",
            pill=("ok", "LOADED") if face_ready else ("bad", "NOT FOUND"),
            sub=f"{sum(1 for m in models if m['exists'])}/{len(models)} artifacts on disk"),
        screens.status_card_html(
            "Signing PKI", "INITIALIZED" if actions.pki_loaded() else "NOT SET UP",
            pill=("ok", "LOADED") if actions.pki_loaded() else ("neutral", "LAZY INIT"),
            sub="Demo authority · ECDSA P-256"),
        screens.status_card_html(
            "Ledger chain", "INTACT" if chain_ok else f"BROKEN AT #{broken_at}",
            pill=("ok", "VERIFIED") if chain_ok else ("bad", "TAMPERED")),
        screens.status_card_html(
            "Cases logged", str(len(records)),
            pill=("bad", f"{critical} CRITICAL") if critical else ("neutral", "THIS SESSION"),
            sub=f"{high_review} requiring review" if high_review else "none requiring review"),
    ]), unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown(
            "<div class='bsx-tier-head'>Controlled attack simulation "
            "<span style='font-family:var(--font-mono);font-size:0.74rem;color:var(--text-3);"
            "border:1px solid var(--line);border-radius:2px;padding:0.2rem 0.5rem;letter-spacing:0.12em;'>"
            "DEMO ENVIRONMENT</span></div>", unsafe_allow_html=True)
        st.caption("Six controlled experiments, not six travellers. Each card builds a synthetic document "
                    "with one specific thing wrong with it, screens it through the real pipeline, and writes "
                    "a real case record. The tag on each card names the layer that should catch it.")
        st.write("")
        cols = st.columns(6)
        specs = [
            ("scn_genuine", "SCN_01", "ALL TIERS", "Genuine document", None,
             "The untouched synthetic document. Every tier should pass, clearing at LOW."),
            ("scn_dob", "SCN_02", "T1 RULES", "Change of birth date", "A",
             "VIZ date of birth edited; MRZ left untouched. Caught by cross-zone consistency, "
             "which floors the verdict at CRITICAL."),
            ("scn_photo", "SCN_03", "T0 CRYPTO / T2 FORENSICS", "Replace the portrait", "B",
             "Portrait swapped, feathered seam. Caught by forensics AND the signed-manifest "
             "integrity check."),
            ("scn_recapture", "SCN_04", "T2 FORENSICS", "Screen recapture", "C",
             "Simulated screen/print recapture. Forensics-only signal -- routes to AMBER, never RED."),
            ("scn_face", "SCN_05", "T2 BIOMETRIC", "Face mismatch", "FACE",
             "Needs a second, different person's real photo -- see the disabled button for why "
             "this one is blocked in this build."),
            ("scn_sig", "SCN_06", "T0 CRYPTO", "Break the signature", "SIG",
             "Hand-tamper an already-signed manifest. Signature fails -- CRITICAL, no model consulted."),
        ]
        for col, (key, sid, layer, title, code, desc) in zip(cols, specs):
            with col:
                with st.container(key=key):
                    st.markdown(screens.scenario_card_head_html(sid, layer, title, desc),
                                 unsafe_allow_html=True)
                    if code == "FACE":
                        st.button("Run scenario", key=f"{key}_btn", use_container_width=True, disabled=True,
                                   help="Blocked: needs a SECOND, different person's real photo. One real "
                                        "identity is on file in data/portraits/ (live face MATCH already "
                                        "verified working via New Screening) -- a genuine mismatch demo needs "
                                        "someone else's photo too, not just this one person's.")
                    elif st.button("Run scenario", key=f"{key}_btn", use_container_width=True):
                        if code is None:
                            actions.run_and_log(actions.GENUINE, None)
                        elif code == "SIG":
                            actions.break_signature_attack()
                        else:
                            actions.run_and_log(actions.ATTACKS[code], code)
                        st.session_state.page = "case"
                        st.rerun()

    st.write("")
    with st.container():
        st.markdown("<div class='bsx-tier-head'>Recent cases</div>", unsafe_allow_html=True)
        st.markdown("<div class='bsx-scroll-x'>" + screens.recent_cases_table_html(records) + "</div>",
                     unsafe_allow_html=True)


def render_capture() -> None:
    chain_ok, _ = ledger_module.verify_chain()
    st.markdown(screens.topbar_html(
        "New screening", "Present a document and, optionally, the face of the person carrying it.",
        eyebrow="Intake", chain_ok=chain_ok), unsafe_allow_html=True)

    # index=0 only seeds the very first render; the dashboard's mode buttons
    # (render_dashboard) set st.session_state.screening_mode_radio directly
    # before rerunning, which Streamlit adopts over `index` on every render
    # after the key already exists.
    mode = st.radio("Screening mode", ["Demo Document", "Real Document"], index=0,
                     horizontal=True, label_visibility="collapsed", key="screening_mode_radio")

    if mode == "Real Document":
        _render_real_document_capture()
        return

    st.caption(
        "This pipeline reads the UTO demo template's exact 1000×700 layout, not arbitrary real-world "
        "documents -- general document detection/OCR is out of scope for this prototype. Edit one of the "
        "Attack Wall PNGs yourself (crop a field, paste a different photo) and upload it here, or switch to "
        "Real Document above for an arbitrary upload."
    )
    # A keyed widget's value lives in st.session_state under that key even
    # before the widget is re-rendered this run, so the step bar can read
    # "is a document already on file" before st.file_uploader is called
    # below -- the standard Streamlit pattern for a progress readout that
    # sits above the widget driving it.
    _doc_ready = st.session_state.get("capture_doc_uploader") is not None
    st.markdown(screens.step_bar_html([
        ("Document", "done" if _doc_ready else "active"),
        ("Person — optional", "active" if _doc_ready else ""),
        ("Screen", "active" if _doc_ready else ""),
    ]), unsafe_allow_html=True)
    col_doc, col_face = st.columns(2, gap="large")
    with col_doc:
        with st.container():
            st.markdown(screens.step_head_html(1, "Document", "active"), unsafe_allow_html=True)
            uploaded_doc = st.file_uploader("Upload an edited UTO document (PNG, 1000×700)", type=["png"],
                                              key="capture_doc_uploader")
    with col_face:
        with st.container():
            st.markdown(screens.step_head_html(
                2, "Live identity — optional",
                "active" if uploaded_doc is not None else ""), unsafe_allow_html=True)
            live_capture = st.camera_input("Live face capture (optional -- for face verification)")
            if live_capture is None:
                live_capture = st.file_uploader("...or upload a face photo instead", type=["png", "jpg", "jpeg"],
                                                  key="face_upload")

    doc_ok, face_present = uploaded_doc is not None, live_capture is not None
    st.markdown(
        "<div class='bsx-pill-row' style='border-top:1px solid var(--line);padding-top:1rem;margin-top:1.4rem;'>"
        f"<span class='bsx-status-dot'><span class='dot {'ok' if doc_ok else 'bad'}'></span>"
        f"Document: {uploaded_doc.name if doc_ok else 'none'}</span>"
        f"<span class='bsx-status-dot'><span class='dot {'ok' if face_present else 'bad'}'></span>"
        f"Live capture: {'provided' if face_present else 'none'}</span>"
        "</div>", unsafe_allow_html=True)

    if doc_ok:
        doc_img = Image.open(uploaded_doc).convert("RGB")
        if doc_img.size != DOC_SIZE:
            st.error(f"Expected a {DOC_SIZE[0]}×{DOC_SIZE[1]} image (the UTO template's own canvas size), "
                      f"got {doc_img.size[0]}×{doc_img.size[1]}. This pipeline reads fixed pixel coordinates, "
                      f"not an arbitrary layout.")
        elif st.button("Screen this document", type="primary", icon=":material/play_arrow:"):
            custom_path = PATHS["documents"] / "_uploaded_custom.png"
            doc_img.save(custom_path)
            face_signal, live_bgr = None, None
            if face_present:
                live_bgr = actions.cv2_bgr_from_upload(live_capture)
                doc_bgr = actions.cv2_bgr_from_upload(uploaded_doc)
                face_signal = face_verify(doc_bgr, live_bgr)
            actions.run_and_log(custom_path, "CUSTOM", extra_signals=[face_signal] if face_signal else None)
            if live_bgr is not None:
                st.session_state.last_live_face_bgr = live_bgr
            st.session_state.page = "case"
            st.rerun()


def _render_real_document_capture() -> None:
    """Mode B: an arbitrary uploaded document, screened by
    core.realdoc.pipeline -- capability-aware, never assumes the UTO
    template. Nothing here is written to disk: uploads are decoded straight
    to in-memory arrays (same privacy stance as actions.cv2_bgr_from_upload
    for live captures) and the result lives only in st.session_state for
    this session, never appended to the demo ledger -- see PLAN_realdoc.md
    for why real, potentially personal documents are kept out of the
    hash-chained audit trail that Mode A's synthetic cases use."""
    st.caption(
        "Upload any identity document or educational record. Every check below only runs when the "
        "document actually supports it -- a marksheet with no photo will correctly show biometric "
        "comparison as NOT APPLICABLE rather than a fabricated result. PDF is rendered from its first "
        "page only (core/realdoc/loader.py); a multi-page scan needs its relevant page split out first."
    )
    _doc_ready = st.session_state.get("realdoc_upload") is not None
    _screened = "realdoc_verdict" in st.session_state
    st.markdown(screens.step_bar_html([
        ("Document", "done" if _doc_ready else "active"),
        ("Person — optional", "active" if _doc_ready else ""),
        ("Screen", "done" if _screened else ("active" if _doc_ready else "")),
    ]), unsafe_allow_html=True)
    col_doc, col_face = st.columns(2, gap="large")
    with col_doc:
        with st.container():
            st.markdown(screens.step_head_html(1, "Document", "active"), unsafe_allow_html=True)
            doc_file = st.file_uploader("Upload a document (PNG, JPG, JPEG, PDF)", type=["png", "jpg", "jpeg", "pdf"],
                                          key="realdoc_upload")
            manual_bbox = None
            if doc_file is not None:
                doc_bgr = loader.load_bgr(doc_file.getvalue(), filename_hint=doc_file.name)
                h, w = doc_bgr.shape[:2]
                st.image(cv2.cvtColor(doc_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)
                st.caption(f"{w}×{h}px · {doc_file.type or 'unknown type'} · original preserved, not resized")
                with st.expander("Portrait detection uncertain? Manually specify the region"):
                    st.caption("Only needed if automatic detection misses the portrait or picks the wrong "
                                "region -- this changes WHERE forensics/face comparison look, it can't make "
                                "a genuinely blurry printed photo sharper.")
                    use_manual = st.checkbox("Use a manually specified region instead of auto-detection",
                                               key="realdoc_manual_toggle")
                    if use_manual:
                        mc1, mc2, mc3, mc4 = st.columns(4)
                        x0 = mc1.number_input("x0", 0, w, 0, key="realdoc_mx0")
                        y0 = mc2.number_input("y0", 0, h, 0, key="realdoc_my0")
                        x1 = mc3.number_input("x1", 0, w, w, key="realdoc_mx1")
                        y1 = mc4.number_input("y1", 0, h, h, key="realdoc_my1")
                        if x1 > x0 and y1 > y0:
                            manual_bbox = (int(x0), int(y0), int(x1), int(y1))
                            st.image(cv2.cvtColor(doc_bgr[int(y0):int(y1), int(x0):int(x1)], cv2.COLOR_BGR2RGB),
                                       caption="Preview of the manually selected region", width=200)
                        else:
                            st.warning("x1/y1 must be greater than x0/y0.")
    with col_face:
        with st.container():
            st.markdown(screens.step_head_html(
                2, "Person verification photo",
                "active" if doc_file is not None else ""), unsafe_allow_html=True)
            person_capture = st.camera_input("Live camera", key="realdoc_camera")
            if person_capture is None:
                person_capture = st.file_uploader("...or upload a face photo", type=["png", "jpg", "jpeg"],
                                                    key="realdoc_face_upload")
            person_bgr = actions.cv2_bgr_from_upload(person_capture) if person_capture is not None else None
            if person_bgr is not None:
                st.image(cv2.cvtColor(person_bgr, cv2.COLOR_BGR2RGB), use_container_width=True, width=220)

    if doc_file is None:
        return
    if st.button("Screen this document", type="primary", icon=":material/play_arrow:", key="realdoc_screen_btn"):
        with st.spinner("Running OCR, classification, forensics and biometric comparison..."):
            verdict, ctx = screen_real_document(doc_bgr, person_bgr=person_bgr, manual_portrait_bbox=manual_bbox)
        st.session_state.realdoc_verdict = verdict
        st.session_state.realdoc_ctx = ctx
        st.session_state.realdoc_doc_bgr = doc_bgr
        st.session_state.realdoc_person_bgr = person_bgr
        st.rerun()

    if "realdoc_verdict" not in st.session_state:
        return
    verdict, ctx = st.session_state.realdoc_verdict, st.session_state.realdoc_ctx
    st.write("")
    st.markdown(f"<div class='bsx-tier-head'>Result — {ctx['doc_type']}</div>"
                 f"<p style='color:var(--text-3);font-size:0.8rem;margin-top:-0.5rem;'>{ctx['doc_type_note']}</p>",
                 unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='bsx-tier-head'>Document Capabilities</div>", unsafe_allow_html=True)
        st.markdown(screens.realdoc_capability_panel_html(ctx["capabilities"]), unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1], gap="large")
    with col_a:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Verification Ladder</div>", unsafe_allow_html=True)
            st.markdown(screens.realdoc_ladder_html(verdict.steps), unsafe_allow_html=True)
        if ctx["portrait_bbox"] is not None:
            with st.container():
                title = "Biometric Comparison" + (" (manually specified region)" if ctx.get("portrait_manual") else "")
                st.markdown(f"<div class='bsx-tier-head'>{title}</div>", unsafe_allow_html=True)
                x0, y0, x1, y1 = ctx["portrait_bbox"]
                cp1, cp2 = st.columns(2)
                with cp1:
                    st.image(cv2.cvtColor(st.session_state.realdoc_doc_bgr[y0:y1, x0:x1], cv2.COLOR_BGR2RGB),
                               caption="Document portrait", use_container_width=True)
                with cp2:
                    if st.session_state.realdoc_person_bgr is not None:
                        st.image(cv2.cvtColor(st.session_state.realdoc_person_bgr, cv2.COLOR_BGR2RGB),
                                   caption="Presented person", use_container_width=True)
                    else:
                        st.info("No person photo provided for this case.")
                face_sig = next((s for s in verdict.signals if s.check == "face_verification"), None)
                if face_sig and "similarity" in face_sig.detail:
                    st.caption(f"Similarity {face_sig.detail['similarity']:.3f} "
                                f"(threshold {face_sig.detail['threshold']:.3f}) — {face_sig.message}")
    with col_b:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>OCR / Field Extraction</div>", unsafe_allow_html=True)
            if ctx["capabilities"]["OCR"]:
                st.markdown(screens.realdoc_fields_table_html(ctx["fields"]), unsafe_allow_html=True)
            else:
                st.info("No readable text detected on this document.")
        if ctx["mrz"].detected:
            with st.container():
                st.markdown("<div class='bsx-tier-head'>MRZ</div>", unsafe_allow_html=True)
                if ctx["mrz"].status == "INSUFFICIENT_QUALITY":
                    st.warning("An MRZ-shaped region was found but couldn't be read with enough confidence "
                                "to trust (scan resolution/skew) — not treated as a checksum failure.")
                else:
                    label = "VALID" if ctx["mrz"].status == "DETECTED_VALID" else "INVALID"
                    st.caption(f"DETECTED + {label}")
                    st.code(f"{ctx['mrz'].line1}\n{ctx['mrz'].line2}", language=None)
                    chips = "".join(
                        f"<span class='bsx-pill {'green' if c.ok else 'red'}' style='margin-right:0.4rem;margin-top:0.4rem;display:inline-block;'>"
                        f"{c.field.upper()}: {'OK' if c.ok else 'FAIL'}</span>" for c in ctx["mrz"].checks)
                    st.markdown(chips, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='bsx-tier-head'>Detected Evidence</div>", unsafe_allow_html=True)
        st.markdown(screens.realdoc_evidence_html(verdict.signals), unsafe_allow_html=True)

    conf_col, _ = st.columns([1, 2])
    with conf_col:
        st.markdown(screens.realdoc_confidence_dial_html(verdict.steps), unsafe_allow_html=True)

    st.markdown(screens.realdoc_verdict_card_html(verdict), unsafe_allow_html=True)


def render_case() -> None:
    """ONE case, ONE page.

    This screen replaces the previous Evidence Analysis / Risk Decision /
    Investigation trio. Those split a single case across three navigation
    destinations, so answering "what is wrong with this document" meant
    clicking between pages and holding the verdict in your head -- and, as
    reported during real-document testing, they silently showed a stale
    unrelated case when the officer was working in Real Document mode.
    A case is one object; it now reads top to bottom as one document:
    verdict, then the ladder that produced it, then the evidence behind
    each finding.
    """
    actions.ensure_active_case()
    verdict, ctx = st.session_state.last_verdict, st.session_state.last_ctx
    path, case_id = st.session_state.active_path, st.session_state.case_id
    chain_ok, _ = ledger_module.verify_chain()
    policy = load_policy()

    st.markdown(screens.topbar_html(
        "Case file", eyebrow=f"Case {case_id} · {Path(path).name}",
        case_chip=f"CASE-ID: {case_id}", chain_ok=chain_ok), unsafe_allow_html=True)

    # 1. THE VERDICT -- the answer first, before any of the evidence that
    #    produced it. An officer reads this and nothing else in the common case.
    st.markdown(screens.verdict_hero_html(verdict, policy["risk_bands"]), unsafe_allow_html=True)
    note = screens.crypto_note(verdict)
    if note:
        st.markdown(note, unsafe_allow_html=True)

    st.write("")
    col_doc, col_right = st.columns([1.15, 1], gap="large")

    # 2. THE EVIDENCE -- the document as presented, flagged.
    with col_doc:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Document as presented</div>", unsafe_allow_html=True)
            has_findings = any(s.severity == Severity.FAIL for s in verdict.signals)
            if has_findings:
                st.image(overlay(str(path), verdict), caption="Flagged regions boxed", use_container_width=True)
            else:
                st.image(str(path), caption=Path(path).name, use_container_width=True)

        portrait_checks = {"photo_region_anomaly", "manifest_match", "face_verification"}
        if any(s.severity == Severity.FAIL and s.check in portrait_checks for s in verdict.signals):
            with st.container():
                st.markdown("<div class='bsx-tier-head'>Portrait comparison</div>", unsafe_allow_html=True)
                cp1, cp2 = st.columns(2)
                x0, y0, x1, y1 = PORTRAIT_BBOX
                with cp1:
                    st.image(ctx["gray"][y0:y1, x0:x1], caption="Document portrait", channels="GRAY",
                               use_container_width=True)
                with cp2:
                    live = st.session_state.get("last_live_face_bgr")
                    if live is not None:
                        st.image(cv2.cvtColor(live, cv2.COLOR_BGR2RGB), caption="Live capture (this session)",
                                   use_container_width=True)
                    else:
                        st.info("No live capture on file for this case.")

    # 3. THE REASONING -- which tier decided, and why.
    with col_right:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Trust ladder</div>", unsafe_allow_html=True)
            st.caption("Four checks, in order of authority. Each row states the question it asks, "
                        "then what it found on this document.")
            st.markdown(screens.verification_sequence_html(verdict), unsafe_allow_html=True)

        if any(s.severity == Severity.FAIL for s in verdict.signals):
            with st.container():
                st.markdown("<div class='bsx-tier-head'>Findings</div>", unsafe_allow_html=True)
                st.caption("Only what actually went wrong on this document — not a list of everything "
                            "the system is capable of checking.")
                st.markdown(screens.finding_cards_html(verdict), unsafe_allow_html=True)

            with st.container():
                st.markdown("<div class='bsx-tier-head'>Score contributions</div>", unsafe_allow_html=True)
                st.caption("How much each finding added to the risk score.")
                weighted_fails = sorted(
                    (s for s in verdict.signals if s.severity == Severity.FAIL and s.weight > 0),
                    key=lambda s: -s.weight)
                # The ruler must fit the largest bar actually on screen, not
                # just policy.yaml's own weights: a crypto manifest failure
                # carries weight=100 (core/crypto/manifest.py), defined in
                # code rather than the YAML, and can exceed every value in
                # policy["risk_weights"] (max 30). Using policy's max alone
                # would clamp a 100-weight bar to the same width as a
                # 30-weight one -- correct value, misleading proportion.
                max_weight = max([*policy["risk_weights"].values(),
                                   *(s.weight for s in weighted_fails)], default=1)
                meters = "".join(
                    screens.meter_row_html(screens.finding_heading(s.check), s.weight, max_weight,
                                             tone="red" if s.weight >= max_weight * 0.6 else "amber")
                    for s in weighted_fails)
                total = sum(s.weight for s in weighted_fails)
                st.markdown(meters or "<p style='color:var(--text-3);font-size:0.85rem;'>No weighted findings.</p>",
                             unsafe_allow_html=True)
                st.markdown(f"<div class='bsx-contrib-total'><span>Total score</span>"
                             f"<span class='amt'>{total}</span></div>", unsafe_allow_html=True)
                if total != verdict.score:
                    st.caption(f"The findings above add up to {total}, but the verdict is "
                                f"{verdict.score}. That is not an error: a decisive check overrode the "
                                f"running total. The note above the document says which one.")

        with st.container():
            st.markdown("<div class='bsx-tier-head'>Pipeline log</div>", unsafe_allow_html=True)
            st.markdown(screens.pipeline_log_html(verdict), unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='bsx-tier-head'>Machine-readable zone</div>", unsafe_allow_html=True)
            st.code(f"{ctx['line1']}\n{ctx['line2']}", language=None)
            mrz_checks = [s for s in verdict.signals if s.check.startswith("mrz_checksum_")]
            st.markdown("".join(
                f"<span class='bsx-pill {'green' if s.severity == Severity.PASS else 'red'}' "
                f"style='margin-right:0.35rem;margin-top:0.4rem;display:inline-block;'>"
                f"{s.check[len('mrz_checksum_'):].replace('_', ' ')}</span>"
                for s in mrz_checks), unsafe_allow_html=True)

        fields = ctx["fields"]
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Extracted identity</div>", unsafe_allow_html=True)
            st.markdown(
                "<div class='bsx-datalist'>"
                f"<div class='bsx-datarow'><span class='bsx-field-name'>Document no</span>"
                f"<span class='bsx-field-value'>{fields.passport_number}</span></div>"
                f"<div class='bsx-datarow'><span class='bsx-field-name'>Nationality</span>"
                f"<span class='bsx-field-value'>{fields.nationality}</span></div>"
                f"<div class='bsx-datarow'><span class='bsx-field-name'>Expiry</span>"
                f"<span class='bsx-field-value'>{fields.date_of_expiry}</span></div>"
                "</div>", unsafe_allow_html=True)


def render_audit() -> None:
    """The ledger across ALL cases -- deliberately a separate destination
    from the case file, because its subject is the audit chain itself,
    not any one screening."""
    records = ledger_module.read_all()
    ok, broken_at = ledger_module.verify_chain()

    st.markdown(screens.topbar_html(
        "Audit trail",
        "Every screening appends a hash-chained record. Editing any past record in place breaks the "
        "chain at exactly that index and the verifier names it.",
        eyebrow="Tamper-evident ledger", chain_ok=ok), unsafe_allow_html=True)

    col_left, col_right = st.columns([1.3, 1], gap="large")
    with col_left:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Chain events</div>", unsafe_allow_html=True)
            if not records:
                st.caption("No events logged yet.")
            else:
                # Real 1-based position in append order (oldest = record 1)
                # -- reversed only for display, so RECORD #n always names
                # the same case no matter how many newer cases arrive.
                indexed = list(enumerate(records, 1))
                for i, record in reversed(indexed[-12:]):
                    st.markdown(screens.audit_record_card_html(record, i, is_head=(i == len(records))),
                                 unsafe_allow_html=True)

    with col_right:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Integrity status</div>", unsafe_allow_html=True)
            # verify_chain() returns a 0-based index; the record cards
            # above number from 1 (RECORD #0001 = oldest), so +1 here
            # keeps this pill naming the SAME record the card above it does.
            pill_cls, pill_txt = ("ok", "Audit ledger — intact") if ok else \
                ("broken", f"Chain broken at record #{broken_at + 1:04d}")
            st.markdown(f"<span class='bsx-chain-pill {pill_cls}'>{pill_txt}</span>", unsafe_allow_html=True)
            st.write("")
            # States what the chain does AND does not prove. Without the
            # second half an officer can reasonably read "intact" as "these
            # documents are genuine" -- it means only that our own record
            # of the screenings has not been edited afterwards.
            st.markdown(
                "<div class='bsx-limits'><div class='k'>What this proves</div>"
                "<p>Each record carries a fingerprint of the one before it, so editing any stored "
                "record breaks the chain from that point on and the verifier names it.<br><br>"
                "<b>It does not prove any document is authentic.</b> It proves our record of the "
                "screening has not been altered after the fact.</p></div>", unsafe_allow_html=True)
            st.write("")
            if st.button("Re-verify chain", icon=":material/verified_user:", use_container_width=True,
                          key="verify_chain_btn"):
                st.rerun()

        with st.container():
            st.markdown("<div class='bsx-tier-head'>Demo utilities</div>", unsafe_allow_html=True)
            st.caption("Rewrite a past verdict by hand, then re-verify: the chain should name the broken record.")
            if st.button("Simulate tampering with a past case", use_container_width=True, key="tamper_btn"):
                if not actions.simulate_tamper():
                    st.warning("Screen at least one document first.")
                else:
                    st.rerun()
            if st.button("Reset ledger", use_container_width=True, key="reset_ledger_btn"):
                actions.reset_ledger()
                st.rerun()


def render_status() -> None:
    """What is actually running, stated plainly. Every value here is read
    live off disk or the ledger -- nothing is a hardcoded version string
    or an invented confidence figure. This is the screen that answers a
    judge's "how do I know this is real" without them having to open a
    terminal."""
    chain_ok, broken_at = ledger_module.verify_chain()
    records = ledger_module.read_all()
    policy = load_policy()
    models = actions.models_status()
    pki = actions.pki_public_info()
    test_n = actions.test_case_count()

    st.markdown(screens.topbar_html(
        "System status",
        "Models, signing authority, policy and ledger, read directly off this machine -- "
        "not a status page someone remembered to update.",
        eyebrow="Verification", chain_ok=chain_ok), unsafe_allow_html=True)

    models_ready = all(m["exists"] for m in models)
    st.markdown(screens.status_grid_html([
        # Named for what they DO, not for the artifact they happen to be.
        # "Model artifacts 4/4" told a judge nothing; "Biometric engine
        # READY" does, and the file-level detail is still one panel below.
        screens.status_card_html(
            "Biometric engine", "READY" if models_ready else "INCOMPLETE",
            pill=("ok", f"{sum(1 for m in models if m['exists'])}/{len(models)} FILES") if models_ready
            else ("bad", "MISSING FILES"),
            sub="Face detection + matching"),
        screens.status_card_html(
            "Cryptographic engine", "READY" if pki else "NOT SET UP",
            pill=("ok", "ECDSA P-256") if pki else ("neutral", "STARTS ON FIRST USE"),
            sub="Signing + signature checks"),
        screens.status_card_html(
            "Ledger chain", "INTACT" if chain_ok else f"BROKEN AT #{broken_at}",
            pill=("ok", f"{len(records)} RECORDS") if chain_ok else ("bad", "TAMPERED")),
        screens.status_card_html(
            "Test suite", str(test_n) if test_n is not None else "N/A",
            pill=("ok", "COLLECTED") if test_n else ("neutral", "UNAVAILABLE"),
            sub="pytest --collect-only, this process"),
    ]), unsafe_allow_html=True)

    st.write("")
    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Biometric engine — files on disk</div>",
                         unsafe_allow_html=True)
            st.caption("The actual face-detection and face-matching model files this app loaded, "
                        "with their real sizes read off this machine.")
            row_parts = []
            for m in models:
                size_txt = f"{m['size_bytes']:,} B" if m["exists"] else "NOT FOUND"
                row_parts.append(
                    f"<div class='bsx-datarow'><span class='bsx-field-name'>{m['label']}</span>"
                    f"<span class='bsx-field-value'>{size_txt}</span></div>")
            st.markdown(f"<div class='bsx-datalist'>{''.join(row_parts)}</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='bsx-tier-head'>Cryptographic engine — signing authority</div>",
                         unsafe_allow_html=True)
            if pki is None:
                st.caption("No PKI on disk yet -- created automatically the first time a document is "
                            "signed or verified (core/crypto/pki.py::load_or_create_pki).")
            else:
                st.caption("Demo signing authority -- a real two-level X.509 chain (ECDSA P-256), but "
                            "OUR OWN trust anchor, not the ICAO Public Key Directory.")
                st.markdown(
                    "<div class='bsx-datalist'>"
                    f"<div class='bsx-datarow'><span class='bsx-field-name'>DSC subject</span>"
                    f"<span class='bsx-field-value'>{pki['dsc_subject']}</span></div>"
                    f"<div class='bsx-datarow'><span class='bsx-field-name'>CSCA subject</span>"
                    f"<span class='bsx-field-value'>{pki['csca_subject']}</span></div>"
                    f"<div class='bsx-datarow'><span class='bsx-field-name'>Curve</span>"
                    f"<span class='bsx-field-value'>{pki['curve']}</span></div>"
                    "</div>", unsafe_allow_html=True)
                st.code(f"DSC  SHA-256  {pki['dsc_fingerprint']}\n"
                         f"CSCA SHA-256  {pki['csca_fingerprint']}", language=None)

    with col_b:
        with st.container():
            st.markdown("<div class='bsx-tier-head'>Risk weights &middot; policy.yaml</div>",
                         unsafe_allow_html=True)
            rows = "".join(
                f"<div class='bsx-datarow'><span class='bsx-field-name'>{k.replace('_', ' ')}</span>"
                f"<span class='bsx-field-value'>+{v}</span></div>"
                for k, v in policy["risk_weights"].items())
            st.markdown(f"<div class='bsx-datalist'>{rows}</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='bsx-tier-head'>Bands &amp; overrides</div>", unsafe_allow_html=True)
            band_rows = "".join(
                f"<div class='bsx-datarow'><span class='bsx-field-name'>{name} ({lo}&ndash;{hi})</span>"
                f"<span class='bsx-field-value'>{action}</span></div>"
                for lo, hi, name, action in policy["risk_bands"])
            st.markdown(f"<div class='bsx-datalist'>{band_rows}</div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:var(--text-2);font-size:0.92rem;line-height:1.6;margin-top:0.9rem;'>"
                "<b>Two hard overrides</b> (core/risk.py), checked before the additive score: "
                "an invalid signature forces CRITICAL regardless of total; a failed T1 rule floors the "
                "verdict at CRITICAL (76). With no rule or signature failure, forensic and biometric "
                "signals alone cap the verdict at HIGH -- they can raise a case for review, never "
                "condemn one on their own.</p>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='bsx-tier-head'>Ledger</div>", unsafe_allow_html=True)
            st.markdown(
                "<div class='bsx-datalist'>"
                f"<div class='bsx-datarow'><span class='bsx-field-name'>Records</span>"
                f"<span class='bsx-field-value'>{len(records)}</span></div>"
                f"<div class='bsx-datarow'><span class='bsx-field-name'>Chain state</span>"
                f"<span class='bsx-field-value'>{'INTACT' if chain_ok else f'BROKEN AT #{broken_at}'}</span></div>"
                "</div>", unsafe_allow_html=True)
            st.code(f"GENESIS  {ledger_module.GENESIS_HASH}", language=None)


# Back-compat: older session_state may still hold one of the three retired
# page ids. app.py maps them onto the merged screens above.
def render_evidence() -> None:
    render_case()


def render_risk() -> None:
    render_case()


def render_investigation() -> None:
    render_audit()
