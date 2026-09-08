# BorderShield AI — Current State (baseline for the final build)

**Written:** 2026-08-30. **Status:** working prototype, selected for the next round. 108/108 automated tests passing. Live at the deployed URL and runnable on localhost.

This is a snapshot of exactly what exists today — every screen, every button, what's real, what's disabled, what's not built. Use it as the starting point for planning the final-round build. It is **not** a roadmap or a Q&A doc — for those, see `docs/team/dossier.html` (answers to judge questions) and `docs/team/run-of-show.html` (the demo script).

---

## 1. The six screens

Fixed sidebar nav, same order top to bottom. Nothing else exists outside these six — no hidden pages, no half-built screens.

### Overview (`ui/pages.py::render_landing`)
**Purpose:** the front page. Explains the idea before showing any live data.

| Element | What it does |
|---|---|
| Hero text | Static copy — the one-line thesis and a short explanation. No data, no button logic. |
| Trust Ladder diagram | Static explanation of the 4 tiers (Crypto / Rules / Forensics / Biometric) and their authority order. Same on every load — not tied to a specific case. |
| **"Open screening command" button** | Navigates to Command Center. |
| **"Screen a document" button** | Navigates to New Screening. |
| "What this is not" section | Static honesty block — synthetic data, demo signing authority, hash-chain not blockchain. |

**Working:** everything. **Nothing on this page reads from a database or the ledger** — it's pure static explanation plus two nav buttons.

### Command Center (`render_dashboard`)
**Purpose:** operational hub. Proof the system is live + one-click demo attacks.

| Element | What it does |
|---|---|
| 4 status cards | **Real**, read live: biometric model files present?, signing PKI initialized?, ledger chain intact?, how many cases logged + how many CRITICAL. |
| 6 scenario cards (the "Attack Wall") | Each is a real button. Click → forges a synthetic document with one specific defect, runs it through the actual pipeline, logs a real case, jumps to Case File. |
| — SCN_01 Genuine document | **Works.** Clean pass, LOW/0. |
| — SCN_02 Change of birth date | **Works.** VIZ/MRZ mismatch → T1 catches it → CRITICAL. |
| — SCN_03 Replace the portrait | **Works.** Caught by forensics AND the signed-manifest check. |
| — SCN_04 Screen recapture | **Works.** Forensics-only signal → AMBER, never RED. |
| — SCN_05 Face mismatch | **Disabled (greyed out button).** Needs a second, different real person's consenting photo, which the team doesn't have on file. Not broken — deliberately blocked, with the reason in the button's tooltip. |
| — SCN_06 Break the signature | **Works.** Hand-tampers an already-signed record; signature fails; CRITICAL with zero AI/forensic input — the flagship crypto demo. |
| Recent cases table | **Real.** Shows every case actually run this session, most recent first. |

### New Screening (`render_capture`)
**Purpose:** where you bring your own document instead of a canned Attack Wall button. Two modes via a radio toggle.

**Mode A — Demo Document:**

| Element | What it does |
|---|---|
| File uploader (PNG only) | Accepts an edited copy of one of the Attack Wall PNGs. Must be exactly 1000×700 (the UTO template's own canvas) or it's rejected with a clear size error. |
| Live camera / face-photo uploader (optional) | Captures a face for biometric comparison against the document portrait. |
| **"Screen this document" button** | Runs the real pipeline on the uploaded image, logs a case, opens Case File. |

**Working, with one real constraint:** this mode only reads the UTO template's fixed pixel layout — it cannot parse an arbitrary real ID. That's by design (see Mode B), not a bug.

**Mode B — Real Document** (`_render_real_document_capture`):

| Element | What it does |
|---|---|
| File uploader (PNG/JPG/JPEG/PDF) | Accepts **any** identity or educational document. PDF renders its first page only. |
| Manual portrait-region override (expander) | Lets you draw a bounding box by hand if auto-detection misses the photo. Doesn't sharpen a blurry photo — just fixes *where* forensics/face-match look. |
| Live camera / face-photo uploader (optional) | Same as Mode A. |
| **"Screen this document" button** | Runs OCR, classification, rule checks, forensics, and (if a photo was given) face comparison. Result renders inline on this same page — does **not** navigate to Case File and does **not** get logged to the audit ledger (real documents are never persisted, by design — privacy). |
| Result: Document Capabilities panel | **Real**, per-document. Shows which of 7 checks actually applied to *this* document (OCR / MRZ / Portrait / Face comparison / Rule validation / Forensics / Cryptographic check) — a marksheet with no photo correctly shows Face Comparison as NOT APPLICABLE. |
| Result: Verification Ladder | Two-line format per check (`Checks:` / `This case:`), same language rules as Case File. |
| Result: two-column verdict | "What we established" vs "What we could not establish" — never says "genuine", says "No adverse signals" instead. |

**Working.** Verified against real photos and real everyday documents (a passport, marksheets, IDs) during development — not a mocked path.

### Case File (`render_case`)
**Purpose:** the full result of one screening. The single most important screen.

| Element | What it does |
|---|---|
| Verdict hero | Score /100, band, recommended action. Colour = the band's traffic-light colour, nothing else. |
| Crypto note | Only appears when a signature/manifest check forced the verdict — states that plainly. |
| Document image | The uploaded/attacked image, with flagged regions boxed if anything failed. |
| Portrait comparison | Shown only if a portrait-related check failed — document portrait vs. the live capture on file for this case. |
| Trust ladder (4 rows) | Each row: `Checks:` (constant question) + `This case:` (actual result) + Pass/Fail/N/A. |
| Findings | Only the checks that actually failed, each with a plain-English explanation and the technical wording behind a "Technical detail" toggle. |
| Score contributions | Bar per weighted finding + running total, with a note when a hard override (not the additive sum) decided the verdict. |
| Pipeline log | Full line-by-line technical trace of every signal the pipeline evaluated, in tier order. Scrolls horizontally inside its own box. |
| Machine-readable zone | The document's raw MRZ text + per-field checksum pills. |
| Extracted identity | Document number, nationality, expiry, read straight from the document. |

**Working.** This screen only exists for Mode A / Attack Wall cases — Mode B results render inline on New Screening instead (see above).

### Audit Trail (`render_audit`)
**Purpose:** the tamper-evident ledger across every case run this session.

| Element | What it does |
|---|---|
| Chain events list | Up to the last 12 cases, each as a card with its hash fingerprint, newest first. |
| Integrity status pill | **Real** — INTACT or names the exact broken record index. |
| "What this proves" box | States both halves: catches in-place edits; does **not** prove any document is authentic. |
| **"Re-verify chain" button** | Re-runs the integrity check and reruns the page. |
| **"Simulate tampering with a past case" button** | **Works.** Hand-edits the oldest record's band, then the chain correctly shows broken from that point. Demo-only, clearly labelled. |
| **"Reset ledger" button** | **Works.** Deletes all logged cases, starts clean. Useful before a live demo. |

**Known, disclosed limitation (not a bug):** the chain proves in-place edits were made; it does **not** currently detect someone deleting the most-recent record(s) outright (a truncated file is self-consistent). Documented in `core/crypto/ledger.py`'s own docstring — not hidden, not yet fixed.

### System Status (`render_status`)
**Purpose:** proof nothing is faked, for a technical reviewer specifically.

| Element | What it does |
|---|---|
| 4 engine cards | Biometric engine, Cryptographic engine, Ledger chain, Test suite — each READY/INTACT (or not), every number read live off disk/the ledger/a real `pytest --collect-only` subprocess. |
| Biometric engine file list | Real file names + real byte sizes of the 4 model/cache files on disk. |
| Cryptographic engine panel | Demo signing authority's real certificate subjects + SHA-256 fingerprints (public certs only — private keys are never read or shown). |
| Risk weights table | Live from `core/rules/policy.yaml` — not hardcoded in the UI. |
| Bands & overrides | The 4 risk bands + the 2 hard override rules, stated in words. |
| Ledger panel | Record count, chain state, genesis hash. |

**Working**, entirely read-only — no buttons that change state.

---

## 2. What's disabled or not built (be upfront about these)

| Item | State | Why |
|---|---|---|
| **Face Mismatch demo (SCN_05)** | Disabled button | Needs a second, different, consenting person's real photo. Live face MATCH is verified working (New Screening); a genuine mismatch demo needs someone else's photo too. |
| **Issuer Registry** ("was this document actually issued by the government?") | **Not built** | Would need a connection to a real government records system that doesn't exist and that no one outside government can access. Deliberately not faked — see the Dossier's §3 on why this is a different question from "is it internally consistent" and "was it tampered with". |
| **Real Document mode → Cryptographic check** | Always NOT APPLICABLE | An arbitrary uploaded document has no registered demo signature — nothing to check against. |
| **Real Document mode → results in the audit ledger** | Not logged | Deliberate privacy choice — real, potentially personal documents are never written to disk or the ledger. Only synthetic Attack Wall cases are logged. |
| **Ledger tail-truncation detection** | Not built | The chain catches edits to existing records; it doesn't yet catch someone deleting the newest record(s) and stopping. Disclosed in code and in the Dossier. |
| **ELA (Error Level Analysis) forensic check** | Shown, never scored | Included for completeness and because judges ask about it, but it's a known-unreliable technique — labelled as such, never contributes to the risk score. |
| **General document scanning** | Out of scope | Mode A only reads the exact 1000×700 UTO template layout. Mode B is the general path, with its own honest capability-per-document reporting. |

---

## 3. Test coverage & deployment

- **108 automated tests**, all passing — 82 covering Mode A (checksums, crosszone, rules, risk fusion, all 4 forensic detectors, crypto, ledger tamper-detection), 26 covering Mode B (arbitrary documents, portrait discovery, real face MATCH/MISMATCH, MRZ status model, field-extraction guards).
- **Deployed** on Streamlit Community Cloud (not Vercel — Streamlit needs a persistent process, which serverless can't run). Auto-redeploys on every push to `master`.
- **Runs on localhost** with `git clone` → `venv` → `pip install -r requirements.txt` → `streamlit run app.py`. No manual downloads — the demo documents and AI models are committed to the repo.

## 4. Tech stack, in one line each

- **App/UI:** Python, Streamlit
- **Computer vision:** OpenCV, ONNX Runtime (YuNet face detection + SFace face recognition, both from OpenCV Zoo)
- **OCR (Mode B):** RapidOCR
- **PDF:** PyMuPDF
- **Cryptography:** Python `cryptography` library — real X.509 certs, ECDSA P-256
- **Policy:** `core/rules/policy.yaml` — every weight/rule is config, not hardcoded

---

*For the "why" behind any of this (architecture, cryptography, scoring, rehearsed answers to hard questions), see `docs/team/dossier.html`. For the live demo script, see `docs/team/run-of-show.html`.*
