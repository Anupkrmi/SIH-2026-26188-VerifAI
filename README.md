# BorderShield AI — SIH 2026, PS 26188

**AI-Based Fake Identity & Document Screening System**
Ministry of Home Affairs · Sashastra Seema Bal (SSB) · Category: Software · Theme: Blockchain & Cybersecurity

**Status: working prototype.** All 6 console screens run end-to-end against real generated attacks; 108/108 tests passing. Read this file top to bottom before touching code — it's the fastest path to a running app.

## The one-line thesis

> **Everyone else builds a classifier. We build a trust hierarchy — cryptography decides first, deterministic rules decide second, machine learning only advises and can never condemn a document by itself.**

Three findings drive every design decision here (full sources in `docs/01-RESEARCH.md`):

1. The best industrial forgery detectors score ~26.5% EER on unseen documents. A verdict that depends on a CNN being right is not deployable — ours never does.
2. Generative AI struggles to forge non-Latin scripts convincingly ("Script-Dependent Generative Instability"). Out of scope for this build, but it's why Indian-script documents are a defensive asset, not just a harder case.
3. A model can raise a document for a human to look at. It can never, on its own, tell a human the person in front of them is a fraud. That rule is enforced in code (`core/risk.py`), not just in the pitch deck.

## Quickstart

```powershell
# 1. Clone and enter the repo
git clone https://github.com/Rajveer-code/sih-2026-bordershield.git
cd sih-2026-bordershield

# 2. Environment
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# 3. Verify the build
.\venv\Scripts\python.exe -m pytest tests/ -q      # expect 108 passed

# 4. Run the console
.\venv\Scripts\python.exe -m streamlit run app.py
```

Nothing else to set up. The demo passport, the 3 forged attacks, and the AI models
(`models/*.onnx`, `models/*.npz`) are already committed to the repo — a fresh clone
works immediately, no manual downloads and no font-dependent regeneration step.

## Deploying

**Streamlit Community Cloud** (free, built for this exact stack) — not Vercel: Streamlit needs a
persistent WebSocket-backed process, which serverless/edge platforms structurally can't run.

1. Push this repo to GitHub (already done if you're reading this from there).
2. [share.streamlit.io](https://share.streamlit.io) → **New app** → pick this repo/branch, main
   file path `app.py`.
3. Nothing else to configure: `requirements.txt` and `packages.txt` (system libs — `libgl1` /
   `libglib2.0-0`, needed for `opencv-contrib-python` on the Linux container) are both already
   in the repo root and picked up automatically. `.streamlit/config.toml` sets the theme + headless
   mode, also automatic.
4. The demo corpus (`data/documents/`, `data/forged/`) and models (`models/*.onnx`, `models/*.npz`)
   are committed (see the folder map below for why) — the app works on a fresh clone with zero
   local generation step. `data/pki/` (signing keys) stays gitignored and lazy-initializes on the
   deployed instance's first screening — that's by design, not a missing step.
5. First boot installs `opencv-contrib-python`/`onnxruntime`/`rapidocr-onnxruntime` from
   `requirements.txt`, which takes a few minutes the first time. Subsequent restarts are fast
   (cached).

## What this is NOT

- **Not a general document scanner.** The pipeline reads one fixed 1000×700 layout (the UTO demo passport template it generates itself) at fixed pixel coordinates. It will not parse a real passport, Aadhaar, PAN, or DL photo — that's explicitly out of scope for this build (see `docs/06-VERIFY-QUEUE.md`). Don't feed it real ID scans expecting a result; it'll just misread the MRZ.
- **Not using real ICAO Passive Authentication or the PKD.** Crypto integrity is a real X.509 chain + real ECDSA signatures, but the trust anchor is our own demo signing authority, not a government's. Labelled everywhere it surfaces in the UI.
- **Not a blockchain.** The audit trail is a hash-chained JSONL file. Real tamper-evidence for in-place edits, honestly documented limitation against tail-truncation (`core/crypto/ledger.py` docstring).

## Architecture — the Trust Ladder

```
T0  Cryptographic signature   decisive BOTH ways   core/crypto/
T1  MRZ + rules + crosszone   decisive AGAINST only core/mrz.py, core/rules/, core/crosszone.py
T2  Forensics (advisory)      caps at HIGH, never CRITICAL alone   core/forensics/
T2  Biometric face match      caps at HIGH, never CRITICAL alone   core/face/
                     ↓
              core/risk.py fuse() → Verdict (score, band, action)
```

Full rationale for the fusion rule (and the two real bugs it took to get right) is in `core/risk.py`'s own docstring — read it before changing anything there.

### UI language rules (do not regress these)

The console had a real readability failure: it printed a tier's *standing description* and that tier's *per-case result* in the same slot, so "capture shows moiré/blockiness consistent with a screen recapture" read as a finding about the document on screen when it was a description of what the layer looks for. The fix is structural and must be preserved.

| Rule | Where it lives |
|---|---|
| Every ladder row renders **two labelled lines**: `Checks:` (the constant plain-English question, never changes with the result) and `This case:` (the actual outcome). | `screens._TIER_QUESTION`, `screens._REALDOC_QUESTION` |
| Correct-but-unreadable wording is mapped to plain English, and the **original is kept** behind a `Technical detail` disclosure — demoted, never deleted. | `screens.plain_message()`, `.bsx-tech` |
| A real-document score of 0 renders **"No adverse signals"**, never "clean"/"genuine"/"authentic". Issuer authenticity is not established by this system, so that claim is unsupported. | `screens.realdoc_verdict_card_html()` |
| Real-document results show **both halves**: what was established, and what could not be — each read off the live ladder, never a fixed list. | `.bsx-split` |
| `REVIEW` is neither pass nor fail and says *why* it is a review (advisory layer, costs no risk points). | `screens._REALDOC_REVIEW_REASON` |
| Audit Trail states what the chain proves **and what it does not** (it never proves document authenticity). | `pages.render_audit()` |
| Officer-facing screens carry no file paths or type names. System Status is the deliberate exception — it exists for the technical reviewer. | — |

### Folder map

| Path | What's in it |
|---|---|
| `core/` | Mode A's pipeline: MRZ/VIZ reading, crosszone, rules engine, forensics, face verification, crypto (PKI + signed manifest + ledger), risk fusion. |
| `core/realdoc/` | Mode B's separate pipeline (arbitrary real documents): OCR, classification, portrait discovery, best-effort MRZ, field extraction/validation, its own capped risk fusion. See "Real Document Screening" below. Imports from `core/` (reuses forensics + face verification unchanged); nothing in `core/` imports back. |
| `synth/` | Generates the synthetic UTO demo document, the 3 forged attacks (DOB edit, portrait swap, screen recapture), and signs everything. |
| `ui/` | Streamlit console. `style.py` = CSS/design tokens, `screens.py` = pure render functions (data in, markup out, never touches session state), `actions.py` = session-state/ledger logic, `pages.py` = per-screen orchestration wiring the two together. |
| `tests/` | 108 tests, run before every commit. |
| `docs/` | Phase-0 research, strategy, architecture, feature backlog, execution plan. Background/rationale, not setup instructions — this README is the setup doc. |
| `reference/` | The Stitch-generated UI reference design the console's visuals are matched to. |
| `data/documents/`, `data/forged/`, `models/*.onnx`, `models/*.npz` | Committed — deploy needs them present with no local generation step, and `synth/*.py`'s text rendering hardcodes Windows font paths, unusable on a Linux deploy container. |
| `data/pki/`, `data/portraits/`, `results/` | Gitignored. `data/pki/` holds real (if demo-only) private keys; `data/portraits/` holds real consenting-person photos; `results/` is session-local ledger output. |

## The console

6 screens, fixed sidebar nav (visuals: the Sovereign light design system — see `PLAN_redesign.md`/`PLAN_polish.md` for the full rationale):

| Screen | Shows |
|---|---|
| **Overview** | The thesis, the Trust Ladder drawn as a connected diagram, and the honest "what this is not" limits — read once, before operating the console. |
| **Command Center** | 4 real status cards (models/PKI/ledger/cases), the 6-button Attack Wall as scenario cards, recent-cases table. |
| **New Screening** | Mode toggle: **Demo Document** (the UTO template + Attack Wall) or **Real Document** (any arbitrary upload, see below). |
| **Case File** | One case, one page: verdict, the ladder that produced it, evidence/findings, score contributions, the pipeline log, MRZ, extracted identity. |
| **Audit Trail** | Hash-chained ledger records across all cases, chain-integrity verify + tamper-demo utilities. |
| **System Status** | Models, demo signing PKI, `policy.yaml` weights/bands/overrides, ledger state, live test count — read directly off this machine. |

### Attack Wall — what each button actually does

| Button | Attack | Tier that catches it |
|---|---|---|
| GENUINE | Untouched document | Everything passes → LOW |
| CHANGE DOB | VIZ date of birth edited, MRZ left alone | T1 crosszone mismatch |
| REPLACE PHOTO | Portrait swapped with a feathered seam | T2 forensics + T0 crypto (impersonation mode) |
| SCREEN RECAPTURE | Real re-encode + moiré/glare simulation | T2 forensics only — routes to review, never CRITICAL |
| FACE MISMATCH | *(disabled — see below)* | T2 biometric |
| BREAK SIGNATURE | Hand-tampers an already-signed manifest | T0 crypto — CRITICAL, zero forensic/biometric input consulted |

### Face verification — status

**MATCH is verified working** with a real photo (2026-08-28): document portrait vs. a different frame of the same person scored similarity 0.764 against the 0.363 threshold, correctly PASS, folding into a LOW verdict end to end.

The Attack Wall's **FACE MISMATCH** button stays disabled — it needs a *second, different* person's photo, and `data/portraits/` currently holds 3 photos of one identity only. To unblock it:

1. Keep the existing photo(s) in `data/portraits/`, and add at least one **different person's** real, consenting face photo (`.jpg`/`.png`, clear frontal shot).
2. Re-run `python -m synth.passport` — it randomly picks one candidate as the document's baked-in portrait (`synth/passport.py::_load_or_placeholder_portrait`, which now does an aspect-preserving center-crop, not a distorting stretch — see its docstring if the source photo is an unusual aspect ratio).
3. On the **New Screening** screen, upload a *different* person's photo as the live capture for a real MISMATCH demo (already-verified MATCH just needs any two frames of the same person).

`data/portraits/` is gitignored — real faces never get committed. Don't put anyone's actual passport/Aadhaar/ID scan through this pipeline expecting a real result (see "What this is NOT," above) — it only ever wants a face crop, not the document.

## Real Document Screening (Mode B)

A second, separate pipeline (`core/realdoc/`) alongside Mode A's fixed-template one. Upload *any* document — passport, college ID, marksheet, driving licence, whatever — at its own native resolution, no 1000×700 requirement, nothing resized destructively. Switch to it via the mode toggle at the top of **New Screening**.

It is **capability-aware**: every check only runs when the document actually supports it, and says so explicitly rather than guessing.

| Capability | How it's decided |
|---|---|
| OCR | [RapidOCR](https://github.com/RapidAI/RapidOCR) (ONNX runtime backend — no torch/paddle, installed with `--no-deps` + only its non-cv2 dependencies, specifically to avoid a second `cv2` package colliding with `opencv-contrib-python`; verified side-by-side). Real text, real confidence scores, off any document. PDF uploads are rendered from page 1 via PyMuPDF (`core/realdoc/loader.py`) — no Poppler binary needed. |
| Document type | Best-effort: a *confidently-read* MRZ → PASSPORT; else OCR keyword hits (AADHAAR, COLLEGE, MARKSHEET, ...); else aspect ratio; else `UNKNOWN`. A low-confidence MRZ-shaped read does NOT count as passport evidence (dense body text on a certificate can trip the locator too) — never claimed as more certain than that. |
| Field extraction | Regex/keyword over the OCR text (name, DOB, doc number, dates, institution). Every field reports `EXTRACTED` / `UNCERTAIN` / `NOT_DETECTED` with a confidence bucket — never a guessed value. Guards against hallucination: a label with no value of its own never borrows the next field's label text; a free-text field (name/nationality) never accepts a numbers-only grab; a gender field only accepts an actual M/F/MALE/FEMALE token. |
| MRZ | Four states, not a boolean — `NOT_DETECTED`, `INSUFFICIENT_QUALITY`, `DETECTED_VALID`, `DETECTED_INVALID` (`core/realdoc/mrz_scan.py`). Reuses `core/mrz.py`'s real ICAO checksum math; its band-locator fallback was rebounded to grow outward from the single densest text row rather than take every row above a loose 30%-of-peak floor (a real scanned page returned an 869px/37%-of-page band under the old logic — see commit history). `try_read_mrz_robust()` additionally retries against a document-boundary-cropped-and-deskewed version of the page (`core/realdoc/page_crop.py`) when the page has visible margin around the actual document. |
| Portrait | Full-page YuNet scan (`core.face.pipeline.detect_faces`, additive — the existing single-best `detect_largest_face` used everywhere else is untouched), scored by confidence/size/off-centre position, with a size floor measured against real documents (6% of the shorter side, or `MIN_FACE_SIZE`, whichever is larger — a marksheet seal graphic hit 93% YuNet confidence at 4% size, real ID portraits ran 10–23%). No plausible candidate → biometric comparison is skipped outright. An officer can override with a manually-specified region (4 plain number inputs, no new UI dependency) when auto-detection is absent or visibly wrong — it changes *where* the checks look, it cannot fix a genuinely low-quality source photo. |
| Biometric | The **same** `core.face.pipeline.verify()` used by Mode A — detect → quality gate → SFace embed → cosine match — unchanged, called on the full document (or the manual crop) + the presented photo. |
| Forensics | The same four detectors Mode A uses (`photo_region`, `noise`, `recapture`, `ela`), but a FAIL from the first three is downgraded to an advisory WEAK signal (zero score weight) in this mode specifically — their thresholds were calibrated only against the synthetic UTO template's one portrait geometry, and validating against 6 real documents showed a 100% false-positive rate on `photo_region_anomaly` before this fix. `ela` was already permanently advisory in Mode A. |
| Cryptographic integrity | Always `NOT APPLICABLE` — an uploaded real document has no registered demo signature, and this mode never pretends otherwise. |

**Risk fusion is separate from Mode A's** (`core/realdoc/risk.py`, not `core/risk.py`): pure additive scoring against the same `policy.yaml` bands, but it **cannot reach CRITICAL** (that band is reserved for a decisive cryptographic proof Mode A can produce and Mode B structurally cannot — asserted by a test), and returns **REVIEW** instead of a score when there's too little evidence to say anything at all — "could not determine" and "determined to be fine" are kept as different outcomes, never collapsed into one LOW.

**Verified against real documents** (passport, college ID, 10th/12th marksheet, a university marksheet, Aadhaar — never committed, see Privacy below): passport classified `PASSPORT`, 4 fields extracted (DOB, expiry, name, nationality), face **MATCH at similarity 0.585–0.684 across four different real photos of the same person**, and a genuine **MISMATCH at similarity 0.304** against a second, different, consenting person — same unmodified 0.363 threshold both times, no forcing. All three marksheets correctly classified `EDUCATIONAL DOCUMENT`, no MRZ/face fabricated, no false forensic positives. College ID: portrait and OCR both work; face comparison correctly reports REVIEW because the card's own printed photo fails the blur floor (sharpness 9.6, need ≥40) — traced precisely to the card, not the presented photo, and left uncorrected rather than loosening a shared threshold to force a nicer-looking demo.

**Known, honest limitations**, not yet cleared:

- The one real passport tested has its MRZ genuinely undetected: a focused, multi-technique attempt (bounded locator, page-boundary crop, horizontal-extent trimming, a 7-candidate search across the whole lower half) converged on the same finding — this specific scan has no separable page margin to crop to, and no candidate band anywhere clears the confidence floor. Reported honestly as `NOT_DETECTED`, never a fabricated checksum failure. A from-scratch, resolution-adaptive MRZ segmenter could likely fix this but is out of scope for this build.
- OCR field extraction is regex/keyword based, not a learned extractor — it works well on documents whose fields are explicitly labelled (marksheets, passports) and returns little on ones that aren't (a college ID with just a name and photo; Aadhaar's bilingual layout isn't in the keyword list yet).
- The manual portrait-region override fixes *location* uncertainty only; it cannot make a genuinely blurry printed photo pass the quality gate.

**Privacy**: uploads and camera captures are decoded straight to in-memory arrays, exactly like Mode A's live face capture — never written to disk. Mode B results are session-only (`st.session_state`), not appended to the hash-chained ledger; that ledger's audit-trail design is for Mode A's synthetic demo cases, and extending it to real, potentially personal documents was a deliberate scope decision, not an oversight. Real documents used to validate this mode were read directly from a local folder outside this repo and never copied in — `data/portraits/` (gitignored) holds only face crops for the biometric demo, never a document scan.

## Testing

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -q
```

108 tests: 82 covering Mode A (MRZ checksums, crosszone, rules, risk fusion, all 4 forensic detectors, crypto, ledger tamper-detection, the evidence heatmap) + 26 covering Mode B (`tests/test_realdoc.py` — arbitrary dimensions, portrait discovery, real face MATCH across 4 photos, a **genuine** real-second-identity MISMATCH end-to-end plus a forced-threshold logic test kept alongside it, quality-gate REVIEW, the 4-way MRZ status model, MRZ/crypto correctly N/A, field-extraction hallucination guards, page-boundary cropping, band-capping). Run this before every commit — CI-equivalent until an actual CI is set up.

## Hard rules for this repo

1. **No invented numbers.** Every figure shown anywhere traces to a real file in `results/`, `core/rules/policy.yaml`, or a cited source. Unknown → `[PLACEHOLDER: how to get it]`, never a guess.
2. **No AI attribution** anywhere — commits, code, docs, slides.
3. **Verify before claiming done.** Run it, show the output.
4. All paths/constants come from `config.py`. Never hardcode a path or threshold elsewhere.
5. Nothing goes in a demo or slide that can't be defended live in Q&A.

## Read next

**Start here if you're on the team, not writing code:**

| Doc | Who it's for |
|---|---|
| [`docs/team/dossier.html`](docs/team/dossier.html) | **Everyone.** Answers any question a judge can ask, in plain English — what the project is, the three questions people mix up, what each screen shows, easy and hard question banks, glossary. Read once before Round 2. |
| [`docs/team/run-of-show.html`](docs/team/run-of-show.html) | **Whoever presents.** What each screen is, then the click-by-click demo script: what to click, what to say, how long, and what to do if something breaks live. |

Both are self-contained HTML — open them in any browser, no server needed.

| Doc | What it settles |
|---|---|
| `docs/01-RESEARCH.md` | The evidence base — every claim above, with its source. |
| `docs/02-STRATEGY.md` | Positioning against other AI-assisted teams. |
| `docs/03-ARCHITECTURE.md` | The Trust Ladder in full, module-by-module. |
| `docs/04-FEATURES.md` | Tiered backlog if there's time left after the internal round. |
| `docs/05-EXECUTION.md` | Demo script, role split, jury Q&A prep. |
| `docs/06-VERIFY-QUEUE.md` | Claims not yet independently verified — clear these before any external presentation. |

These docs predate the final scope cut (they still describe an earlier, larger vision); this README and the actual code in `core/`/`ui/` are the current source of truth whenever they disagree.
