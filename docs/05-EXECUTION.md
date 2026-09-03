# 05 — Execution

## 1. Calendar

Today is **2026-08-26**. Two gates.

| When | Milestone | Owner |
|---|---|---|
| Aug 26 – Sep 5 | Clear the [verify queue](06-VERIFY-QUEUE.md); lock the PPT narrative | Lead + Research |
| Aug 28 – Sep 20 | Phase A build: end-to-end thin slice (T1–T8, E1, E2, E3, E11) | All |
| Sep 10 – Sep 20 | Draft idea PPT, three internal review passes | Lead |
| ~Sep 2026 | **Internal college hackathon** — must be nominated | All |
| **~Sep 30** | **Idea submission on portal — GATE 1** | Lead |
| Oct – Nov | Phase B: differentiators; de-risk W1 (NFC) by end-Oct | All |
| Oct/Nov | Screening results, then mentoring sessions | — |
| **Dec 2026** | **Grand Finale — GATE 2** | All |

Confirm exact dates on sih.gov.in via the SPOC. The public timelines are indicative.

## 2. Six-person role split

Six people, six lanes, no overlap. Each owns their lane's demo segment.

| Role | Owns | Finale demo segment |
|---|---|---|
| **Lead / Integrator** | fusion rule, risk calibration, the pitch, Q&A | opening + closing |
| **Documents** | OCR, MRZ, checksum correction, cross-zone, template registry | Module 1 + 2 |
| **Forensics** | tamper localisation, Devanagari SDGI, recapture, metadata | Module 3 + Attack Wall |
| **Biometrics** | face quality, match, PAD, D-MAD, 1:N dedup | Module 4 |
| **Platform** | Android app, NFC/eMRTD, offline sync, edge inference, latency | W1 + offline moment |
| **Security & Evidence** | ledger, threat model, injection defence, red-teaming, legal compliance | W4 + W6 |

Mandatory: at least one female member per SIH rules. Two mentors.

**Rule:** every member must be able to answer a jury question about *any* module at a one-paragraph level. Jurors deliberately ask the quiet person.

## 3. The idea submission PPT (Gate 1 — this is what we failed last time)

Use the official SIH template and fill **every required heading exactly as named**. "Clarity and detail in the prescribed format" is an explicit scoring criterion — teams lose here for formatting, not for ideas. `[VERIFY]` the SIH 2026 template's exact slide count and headings from the portal before drafting.

Content plan against the standard headings:

**Idea / Proposed Solution**
- Open with the positioning sentence. Then the Trust Ladder diagram — one image that shows the whole thesis.
- State the inversion explicitly: *cryptography first, structure second, pixels last.*

**Technical Approach**
- Modules 1–4 as the PS names them, plus Module 5 (identity graph) and 6 (evidence ledger) marked as answering the PS's own "multiple identities" and "digital trail" bullets.
- Name the stack. Name the standards: ICAO Doc 9303 (Parts for TD1/TD2/TD3 and Part 7 for MRVs), ISO/IEC 30107-3, ISO/IEC 20059:2025, ISO/IEC 29794-5.

**Feasibility and Viability**
- This is where we win the screening. Put the honest number on the slide:
  > *"The best industrial system in the Third Competition on Document Forgery Detection (2026) achieves 26.52% EER on unseen documents. We therefore designed a system that stays safe when the model is wrong."*
- Offline-first, edge inference, few-shot adaptation with ~50 samples, ₹-scale hardware.
- Name the risks and the mitigations (NFC availability, dataset gaps, mocked government APIs).

**Impact and Benefits**
- 1,751 km, 5 states, 15 land ports, Raxaul / Rupaidiha / Jogbani / Sunauli.
- Quantified queue model with stated assumptions — never an invented figure. `[VERIFY]` LPAI throughput.
- Investigation trail; standardised decisions across posts.

**Research and References**
- Cite the 2026 survey, the Third Competition, ICAO Doc 9303, the ISO standards, the SSB mandate and the open-border fact.
- **Most teams leave this slide thin. A dense, real reference slide is the single cheapest way to look like the serious team.**

### PPT rules
- Zero unflagged placeholders. Grep for `[PLACEHOLDER`, `TODO`, `Lorem`, `Your Name` before submitting.
- Every number appears identically everywhere it appears.
- No stock-AI imagery, no purple gradients. One strong architecture diagram beats six icon rows.
- If a number cannot be traced to a source or a result file, it does not go in.

## 4. The finale demo script

Assume a short slot with jurors who have seen a dozen similar systems. Budget roughly:

| Beat | Time | What happens |
|---|---|---|
| 1. The inversion | 45 s | Positioning sentence + Trust Ladder diagram. "Everyone here built a classifier. We built a hierarchy." |
| 2. Cryptographic proof | 90 s | Tap a real e-passport to the phone. Passive Authentication verifies against the country signing chain. Then feed a photoshopped scan of the *same* passport — chip hash mismatch → RED. **No model was involved in that verdict.** |
| 3. The Nepali document | 90 s | Nepali citizenship certificate. Devanagari OCR, `२०५०` converted BS→AD correctly. Show what a naive parser does: a 57-year error. Then the SDGI glyph check catching an AI-inpainted field. |
| 4. Offline | 30 s | Turn on airplane mode. Full verdict still renders. Reconnect; the log syncs. |
| 5. The Attack Wall | 120 s | Eight forgeries, one per taxonomy class, run live. Catch seven. **Show the eighth failing**, name it as a composite attack, cite the competition result, and show it routing to AMBER instead of a false clear. |
| 6. Multiple identities | 60 s | Same face, second document, different name. System raises a biometric alias flag and draws the identity graph. |
| 7. The ledger | 45 s | Try to alter a past decision. Hash chain breaks visibly. "This is the investigation trail the problem statement asks for." |
| 8. Close | 30 s | Restate the fusion rule: *a model in our system can never clear a document and never condemn one — it can only ask for a human.* |

Rehearse until it runs without narration errors. **Record a backup video** of every segment; laptops fail at finales.

## 5. Jury Q&A — prepare these cold

| Question | Answer |
|---|---|
| "What's your accuracy?" | Refuse the framing politely. Give EER/APCER/BPCER at a stated operating point, plus the generalisation gap, and cite that the best industrial system gets 26.5% EER open-set. Then explain why our architecture is safe anyway. |
| "What if your AI is wrong?" | The fusion rule. ML can never clear and never condemn. Show the code. |
| "Isn't ELA discredited?" | Yes. We display it, labelled as a weak legacy signal, and it carries no decisive weight. Here is what actually drives the verdict. |
| "Why blockchain? Isn't it a buzzword here?" | Because no PII goes on it. It is a tamper-evident event log and a shared revocation registry across posts with intermittent connectivity. Storing identities on-chain would be illegal under DPDP. |
| "Where's your data from? Indian IDs aren't public." | Correct — no public dataset covers Indian or Devanagari documents. We state that as a limitation and built a synthetic benchmark with pixel masks, which the 2026 survey names as a gap. |
| "Can this run at a real check post?" | Show the latency table on real hardware and the airplane-mode demo. |
| "Do you connect to Interpol / IVFRT / NCRB?" | No, and we will not claim to. Here is the adapter interface and the API contract; the backend in this demo is mocked and labelled as such. |
| "What about privacy / Aadhaar?" | No Aadhaar number is stored anywhere. Biometric templates are stored only as irreversible transforms. Retention is enforced in code. |
| "What can't you detect?" | Composite attacks, 3D-mask presentation attacks, and a perfectly cloned chip where Active Authentication is absent. Named, with the reasons and the roadmap. |

Practise the last one hardest. **Answering "what can't you do" fluently is the strongest signal of competence available to us.**

## 6. Definition of done

Before the PPT ships:
- [ ] Every `[VERIFY]` cleared or removed from the slide deck
- [ ] Every number traced to a source or a result file
- [ ] Zero placeholders (grep the deck)
- [ ] Template headings match the official format exactly
- [ ] Three people who did not write it have read it for clarity

Before the finale:
- [ ] All eight Attack Wall documents built and reproducible
- [ ] Latency measured on the actual handheld, table generated from a results file
- [ ] Backup demo video recorded per segment
- [ ] Every member can answer a question about every module
- [ ] Offline mode tested with the network genuinely off, not simulated
