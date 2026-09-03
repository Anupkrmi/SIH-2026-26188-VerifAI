# 04 — Feature Backlog

Three tiers. **TABLE-STAKES** = we lose without it. **EDGE** = beats the other teams. **WOW** = the jury remembers us.

Effort is person-days for one competent member. Risk is the chance it does not work in time.

---

## TABLE-STAKES — every rival will have these; ours must be visibly better

| # | Feature | Effort | Risk | How ours differs |
|---|---|---|---|---|
| T1 | Document detection + perspective rectification | 2 | Low | quality gate rejects bad captures instead of guessing |
| T2 | MRZ detection + parse (TD1/TD2/TD3, MRV-A/B) | 3 | Low | all five layouts, not just TD3; visas included per PS |
| T3 | MRZ check-digit validation | 1 | Low | exact ICAO weights 7-3-1 mod 10, incl. composite digit |
| T4 | VIZ OCR for non-MRZ documents | 3 | Med | Devanagari + Nepali, not English-only |
| T5 | Expiry / validity / blacklist rules | 2 | Low | declarative YAML, versioned, auditable |
| T6 | Face detect + 1:1 match to document photo | 2 | Low | quality-gated, reported at a stated FMR |
| T7 | Officer console with per-flag reasons | 4 | Low | field-level reasons, never a bare score |
| T8 | Risk score + GREEN/AMBER/RED | 2 | Low | calibrated + abstention, not a weighted sum |

---

## EDGE — the differentiators. Each maps to a thesis in [02-STRATEGY.md](02-STRATEGY.md)

| # | Feature | Effort | Risk | Why it beats the field |
|---|---|---|---|---|
| **E1** | **Checksum-guided OCR correction** — search the confusion set until check digits validate | 2 | Low | converts OCR from probabilistic to near-deterministic; cheap, clever, demo-able in 20 seconds |
| **E2** | **Cross-zone consistency engine** (VIZ ↔ MRZ ↔ chip ↔ barcode) | 3 | Low | the highest-yield real-world check; what the commercial leader does |
| **E3** | **Bikram Sambat → AD conversion + Devanagari numerals** | 2 | Low | without it every Nepali date is 57 years wrong. Instant credibility with an SSB juror |
| **E4** | **Devanagari glyph-integrity forensics (SDGI)** | 5 | Med | novel, citable, uniquely Indian. See [01-RESEARCH.md §2.2](01-RESEARCH.md) |
| **E5** | **Template geometry registry** (field boxes, fonts, patterns per doc type) | 4 | Low | the real asset behind commercial systems; enables few-shot onboarding of new doc types |
| **E6** | **Few-shot document adaptation** (~50 samples for a new document type) | 4 | Med | Rocamora 2026: EER 3.10% with 50 identities. Operational argument: absorb a new Nepali certificate revision in a day |
| **E7** | **Calibrated risk + conformal abstention** | 3 | Low | the only principled way to have an AMBER band; report ECE/Brier |
| **E8** | **1:N face dedup + identity graph** | 5 | Med | answers the "multiple identities" and "digital trail" PS bullets nobody else touches |
| **E9** | **Transliteration-aware name matching** (ISO 15919 + Indic phonetic keys) | 3 | Med | Soundex fails on Indic names; this is a real operational pain point |
| **E10** | **Offline-first sync** (append-only outbox, airplane-mode verdict) | 4 | Med | the demo moment: turn Wi-Fi off, system still works |
| **E11** | **Metadata + PDF forensics** (EXIF, quant tables, xref incremental updates) | 2 | Low | free wins; nobody does PDF xref history |
| **E12** | **PAD with ISO/IEC 30107-3 metrics** (APCER/BPCER/ACER) | 4 | Med | speaking the standard's language marks us as literate |

---

## WOW — the memorable ones

| # | Feature | Effort | Risk | The moment it creates |
|---|---|---|---|---|
| **W1** | **eMRTD chip read over NFC + Passive Authentication** | 6 | **High** | Hold a real e-passport to the phone. Chip signature verifies. Then show a photoshopped scan of the same passport — chip hash mismatch, instant RED. *Cryptographic proof beats every CNN in the room.* Needs a physical chipped passport — see risk mitigations in [02-STRATEGY.md §6](02-STRATEGY.md) |
| **W2** | **Anti-clone / EF.COM stripping defence** | 2 | Low | Enumerate data groups from the signed SOD, not EF.COM; flag "AA stripped". Cites van Beek 2008 and Calderoni 2014. A 30-second Q&A answer no other team can give |
| **W3** | **The Attack Wall** — 8 self-made forgeries, one per taxonomy class, run live, **including the one we fail** | 5 | Low | The single highest-leverage demo asset. Honesty + citation beats "99% accuracy" |
| **W4** | **Injection-attack defence** (virtual-camera / stream-substitution detection + capture attestation) | 4 | Med | Demo: feed the pipeline a "camera" that is actually a file. Naive systems accept it; ours refuses. This is the 2026 threat class |
| **W5** | **Face morphing detection (D-MAD)** | 5 | High | The frontier border-control attack. Morph two team members' faces, show it verifies against both, then show our detector catching it |
| **W6** | **Tamper-evident evidence ledger** (hash chain + Merkle anchor, no PII) | 4 | Low | "Try to change a past decision." Chain breaks visibly. Delivers the PS's investigation-trail bullet cryptographically |
| **W7** | **Indian/Devanagari forgery benchmark with pixel masks** | 5 | Med | Fills a gap the 2026 survey names explicitly. Publishable; also our honest eval substrate |
| **W8** | **UV/IR hardware adapter demo** (365 nm torch + NoIR camera) | 3 | Med | A software-category team showing a physical security-feature check reads as unusually thorough. Keep strictly optional |
| **W9** | **Subgroup fairness audit of the face stack** | 3 | Low | FMR/FNMR by group with CIs. A government biometric system that audits its own demographic differentials is five years ahead of the room |
| **W10** | **Latency table on real hardware** | 1 | Low | Measured per-stage milliseconds on the actual handheld. Juries almost never see real numbers |

---

## Build order

**Phase A — before the internal hackathon (Sept):** T1–T8, E1, E2, E3, E11. A working end-to-end thin slice beats a pile of disconnected modules. Plus the PPT.

**Phase B — Oct–Nov (if shortlisted):** E4, E5, E7, W1, W2, W6, W10. This is where the differentiators land. W1 must be de-risked by end of October.

**Phase C — finale sprint (Dec):** E6, E8, E9, E10, E12, W3, W4, W9. W3 (Attack Wall) is the last thing built and the first thing rehearsed.

**Cut list if time runs out:** W5 (morphing), W7 (benchmark), W8 (UV/IR) — in that order. Cutting them is fine; each becomes a "designed, not built" slide with a clear rationale, which still scores on future-work.

---

## Anti-features (do not build)

| Tempting | Why not |
|---|---|
| A single end-to-end "is this fake" CNN | Inherits the 26.5% open-set EER and destroys explainability |
| Storing identities/biometrics on a blockchain | Privacy-illegal under DPDP; the theme juror will say so |
| Claiming live Interpol SLTD / IVFRT / NCRB access | We cannot get it. Build the adapter, mock the backend, label it clearly |
| Fingerprint or iris matching | Needs EAC terminal certificates we cannot obtain |
| A chatbot on top of it | Adds nothing to a border decision; costs demo time |
| Real Aadhaar numbers anywhere in the demo | Legal landmine. Use synthetic data only |
