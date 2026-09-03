# 03 — Architecture

## 1. The Trust Ladder

```
                    ┌─────────────────────────────────────────┐
   CAPTURE          │  Handheld (Android) / desk scanner      │
   + attestation    │  camera · NFC · optional UV torch       │
                    └────────────────┬────────────────────────┘
                                     │  signed capture bundle
                    ┌────────────────▼────────────────────────┐
   T0  CRYPTO       │  eMRTD: BAC/PACE → read DGs from SOD    │
   decisive         │  Passive Auth (hash chain → DSC → CSCA) │
                    │  Active Auth (anti-clone)               │
                    │  Aadhaar Secure QR signature            │
                    │  DigiLocker issued-doc fetch            │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
   T1  DETERMINISTIC│  MRZ parse + checksum-guided correction │
   decisive when    │  Cross-zone consistency VIZ↔MRZ↔chip    │
   violated         │  Template geometry registry             │
                    │  Rule engine (expiry, visa, BS→AD)      │
                    │  Blacklist / revocation registry        │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
   T2  FORENSIC ML  │  Tamper localisation (+ mask)           │
   advisory only    │  Devanagari glyph integrity (SDGI)      │
                    │  Recapture: moiré / halftone / screen   │
                    │  Face: quality → match → PAD → morphing │
                    │  Injection-attack detection             │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
   T3  BEHAVIOURAL  │  1:N face dedup across encounters       │
                    │  Identity link graph                    │
                    │  Cross-ICP anomaly                      │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
   FUSION           │  Calibrated risk + abstention band      │
                    │  GREEN / AMBER / RED + per-flag reasons │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
   EVIDENCE         │  Hash-chained append-only event log     │
                    │  Merkle root anchored to permissioned   │
                    │  ledger.  NO PII ON CHAIN.              │
                    └─────────────────────────────────────────┘
```

## 2. The fusion rule (the core IP)

```python
# ponytail: deliberately a small explicit rule table, not a learned fusion model.
# A learned fusion would inherit the 26.5% open-set EER of its weakest input.

def fuse(t0, t1, t2, t3) -> Verdict:
    # T0 is decisive in both directions.
    if t0.crypto_present and t0.passive_auth_failed:
        return RED("chip data does not match its signature")
    if t0.crypto_present and t0.active_auth_absent_but_declared:
        return RED("anti-cloning stripped from index — see van Beek 2008")

    # T1 violations are decisive against, never in favour.
    if t1.hard_violations:
        return RED(t1.hard_violations)      # bad check digit, expired, blacklisted

    # T2 may only raise, never clear.
    band = GREEN
    if t0.crypto_present and t0.all_passed:
        band = GREEN                         # cryptographically proven
    if t2.score > t2.tau_review:
        band = max(band, AMBER)              # ML alone never returns RED
    if t3.alias_detected:
        band = max(band, AMBER)

    # Conformal abstention: if the calibrated interval straddles the
    # decision threshold, refuse to decide.
    if t2.conformal_interval_straddles_threshold:
        band = max(band, AMBER)

    return band
```

Three properties to state out loud in the demo:

1. **ML cannot clear.** A cryptographic or deterministic failure is never overridden by a confident model.
2. **ML cannot condemn.** A model-only signal produces AMBER (officer review), never RED.
3. **The system can say "I don't know."** Conformal abstention gives a stated coverage guarantee instead of a false-confidence number.

## 3. Modules mapped to the problem statement

PS 26188 names four modules. We implement all four and add the ones the PS implies but does not name.

### Module 1 — OCR Extraction *(PS-required)*

| Component | Choice | Why |
|---|---|---|
| Document detect + rectify | corner detection + perspective warp | every downstream check assumes a rectified page |
| MRZ zone | detect → OCR-B constrained decoder (charset `A-Z0-9<`) | closed charset kills most OCR error |
| **Checksum-guided correction** | search confusion set `{0/O, 1/I, 5/S, 8/B, 2/Z}` until all check digits validate | turns probabilistic OCR into near-deterministic parse — **differentiator** |
| VIZ + non-MRZ docs | PaddleOCR / docTR / Surya | Devanagari support `[VERIFY]` |
| Structured extraction | small VLM with constrained JSON output | schema-faithful; SmolVLM2-class is on-device viable |
| Hallucination guard | **VLM output must agree with MRZ + template OCR; disagreement is itself a tamper signal** | never trust a VLM alone |

Extracted fields per PS: passport (name, number, nationality, DOB, expiry, gender); visa (number, type, entry validation, stay duration). MRV-A/MRV-B layouts are ICAO Doc 9303 Part 7.

### Module 2 — Document Validation *(PS-required)*

Policy-as-code. Rules live in versioned YAML, not in `if` statements, so MHA staff can update them without a redeploy and every change is auditable.

```yaml
- id: expiry.six_month_rule
  applies_to: [passport]
  assert: expiry_date >= arrival_date + 180d
  severity: hard
  cite: "carrier/entry validity requirement"

- id: date.bikram_sambat
  applies_to: [np_citizenship, np_licence]
  transform: bs_to_ad(field)      # 57y ahead of AD; 56 during Jan–Mar/Apr
  severity: parse

- id: crosszone.dob
  assert: viz.dob == mrz.dob == chip.dg1.dob
  severity: hard
  reason_template: "VIZ DOB {viz} != MRZ DOB {mrz}"
```

Cross-zone consistency is the highest-yield deterministic check: real forgers edit the printed field and forget the MRZ (or vice versa). It is exactly what the commercial leader does.

### Module 3 — Tampering Detection *(PS calls this "Core AI Innovation")*

PS use cases: photo replacement, text manipulation, stamp forgery, image metadata analysis. Our stack, ordered by reliability:

| Check | Method | Notes |
|---|---|---|
| Template geometry | field bounding boxes, fonts, guilloche reference vs registry | deterministic, cheap, explainable |
| **Devanagari glyph integrity** | shirorekha continuity, matra attachment, conjunct well-formedness, stroke-width consistency | **our novel contribution — exploits SDGI** |
| Photo replacement | edge/blend discontinuity + noise-pattern mismatch at the portrait boundary | classic splicing cues |
| Text manipulation | font/kerning/baseline anomaly + local noise break | catches manual edits |
| Recapture (screen/print) | moiré frequency analysis; halftone structure | the opportunistic class |
| Learned localisation | forensic localisation model producing a **pixel mask** | advisory; mask drives the officer's heatmap |
| Metadata | EXIF/XMP/ICC, JPEG quantisation-table fingerprint; **PDF xref/incremental-update history** | PDF forensics is free and nobody does it |
| ELA | included, **explicitly labelled a weak legacy signal** | pre-empts the forensics juror's objection |

Deliberate: we show ELA *and* say why it is unreliable. That inverts an attack into a credibility gain.

### Module 4 — Face Verification *(PS-required)*

Pipeline order matters — a match score on a bad capture is worse than no score:

```
quality gate (ISO/IEC 29794-5 style)  →  reject bad capture, ask for retake
   ↓
1:1 match  (document photo vs live)   →  report at a stated FMR operating point
   ↓
PAD (ISO/IEC 30107-3)                 →  APCER / BPCER / ACER, not "accuracy"
   ↓
D-MAD morphing detection              →  the frontier attack; MAP per ISO/IEC 20059:2025
   ↓
1:N dedup against encounter index     →  "multiple identities" — the PS bullet everyone skips
```

Note the age problem: a 10-year-old document photo against a live face is a different distribution. Handle with age-tolerant thresholds and state it as a limitation.

### Module 5 (implied, not named) — Identity Graph & Intelligence

The PS asks to *"create a digital trail for investigations and intelligence analysis."* Almost no team will implement this bullet.

- Nodes: encounters, documents, faces, addresses. Edges: same-face, same-doc-number, shared-attribute.
- Detects: same face under two names; one document number against two faces; clusters spanning multiple ICPs.
- **Transliterated-name matching** is the real operational nightmare — Devanagari↔Latin variance (Mohammad/Mohammed/Muhammad, Shrestha/Shreshtha). Soundex is English-only and fails here; use ISO 15919 normalisation + Indic-aware phonetic keys + Jaro-Winkler on normalised forms.

### Module 6 (implied) — Evidence Ledger

Append-only, hash-chained event records; periodic Merkle root anchored to a permissioned ledger. Stores digests and decisions — **never PII, never biometric templates, never an Aadhaar number**.

## 4. Risk scoring — calibrated, not weighted-sum

Every other team ships `0.3a + 0.3b + 0.4c`. We ship:

1. **Calibration** — Platt/isotonic on a held-out split; report **ECE and Brier**, not just AUC.
2. **Conformal abstention** — a stated coverage guarantee, so the AMBER band has a defensible false-clear rate rather than a vibe.
3. **Subgroup audit** — face recognition has documented demographic differentials. Report FMR/FNMR by subgroup with CIs. For a system screening Indian, Nepali, Bhutanese and third-country nationals this is both an ethics and an Article 14 point.
4. **Explicit operating point** — "at FMR = 1e-5" beats "99% accurate" in front of anyone who knows the field.

## 5. Deployment shape

- **Edge-first.** Quantised ONNX / TFLite on an Android handheld; INT8 where it survives. Target a stated end-to-end latency budget per document and **measure it on real hardware** — a latency table is worth more than an accuracy claim.
- **Offline-first sync.** Local encrypted store (SQLCipher-class), outbox + append-only log, conflict-free merge on reconnect. Full verdict in airplane mode.
- **Security.** mTLS, RBAC, no PII in logs, signed model artifacts, SBOM, capture attestation to resist injection attacks.
- **Privacy.** Irreversible/revocable biometric template transforms (ISO/IEC 24745 direction); no Aadhaar number stored; retention limits enforced in code, not in a policy document.

## 6. Stack (choose boring, justify each)

| Layer | Choice | One-line justification |
|---|---|---|
| Handheld app | Android (Kotlin) | NFC for eMRTD is the whole T0 tier; only Android gives it cheaply |
| Inference | ONNX Runtime / TFLite | portable CPU/NPU, quantisation support |
| Backend | Python + FastAPI | team velocity; the ML stack is Python anyway |
| Rules | YAML + a small evaluator | policy-as-code, updatable by non-programmers |
| Store | SQLite/SQLCipher on device; Postgres at the post | offline-first, boring, proven |
| Graph | NetworkX first, Neo4j only if it earns it | YAGNI |
| Ledger | signed Merkle log first; permissioned chain only for the sync demo | a chain that adds nothing is a liability |
| Face | open-weight recognition + FIQA + PAD | see [06-VERIFY-QUEUE.md](06-VERIFY-QUEUE.md) for model selection |
| Console | React | officer review UI, heatmap overlay, graph view |

Hardware target for training: RTX 4060 (8 GB VRAM). Anything that does not fit gets flagged before it is started, not after.
