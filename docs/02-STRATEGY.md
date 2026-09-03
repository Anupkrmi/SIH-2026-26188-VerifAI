# 02 — Winning Strategy

## 0. Start from the honest diagnosis

We were not selected last time. The bottleneck is almost never the code — it is the **idea PPT**, which is screened by people reading dozens of near-identical submissions. So this document optimises two different things, in order:

- **Gate 1 (by ~30 Sept):** get shortlisted. Won on *positioning, specificity, and evidence of homework*.
- **Gate 2 (Dec finale):** win. Won on *a working demo, a defensible architecture, and Q&A survival*.

They need different tactics. Most teams prepare only for Gate 2 and never reach it.

---

## 1. What every other team will build

Predict the field precisely, because we have to beat it. With PS 26188 and an AI assistant, ~90% of teams will converge on:

```
Streamlit/React upload page
  → Tesseract or EasyOCR on the passport image
  → regex to pull MRZ fields
  → ELA (Error Level Analysis) heatmap for "tampering"
  → face_recognition (dlib) for photo match
  → risk_score = 0.3*a + 0.3*b + 0.4*c
  → red/green badge
  → "99.2% accuracy" on a slide
```

Every one of these choices is defensible individually and fatal collectively:

| Their choice | Why it loses |
|---|---|
| ELA as the tampering detector | Weak, noisy, defeated by any recompression; a forensics-literate juror will dismantle it |
| "99.2% accuracy" | The world's best system gets **26.5% EER** on unseen documents. This number is proof of overfitting |
| dlib `face_recognition` | 2017-era; no quality assessment, no liveness, no morphing defence |
| Weighted-sum risk score | Arbitrary weights, uncalibrated, no abstention, unexplainable |
| Laptop + Wi-Fi demo | Not how a border post works |
| Blockchain bolted on ("store IDs on-chain") | Privacy-illegal, and the theme juror will say so |
| Passport-at-an-airport framing | Wrong problem for SSB |

**Our entire strategy is to be the team that knows why each of those is wrong.**

---

## 2. The five theses

### Thesis 1 — Rank evidence by forgeability, not by how impressive the model is

> **The Trust Ladder.** Cryptographic proof outranks deterministic structure, which outranks machine learning, which outranks behaviour.

| Tier | Evidence | Forgeable without? | Role in the verdict |
|---|---|---|---|
| **T0 — Cryptographic** | eMRTD chip Passive Authentication; Aadhaar Secure QR signature; DigiLocker issued-document fetch | a state's private key — **no** | **Decisive** |
| **T1 — Deterministic** | MRZ check digits; VIZ↔MRZ↔chip cross-zone consistency; template geometry; expiry/visa rule engine; BS→AD date conversion; blacklist | yes, but self-checking | **Decisive when violated** |
| **T2 — Forensic ML** | tamper localisation, recapture/moiré/halftone, morphing, PAD | yes | **Advisory only** |
| **T3 — Behavioural** | 1:N face dedup, identity graph, cross-ICP anomaly | hard, requires operational history | Escalation trigger |

**The fusion rule — say this exact sentence to the jury:**

> *"A machine-learning model in our system can never clear a document, and can never condemn one. It can only ask for a human."*

Formally: T2 may raise the risk band but never lower it below what T0/T1 established, and a T2-only signal routes to AMBER (officer review), never to RED (refuse). This is the answer to the question that kills every other team — **"what happens when your AI is wrong?"** — and we answer it architecturally, not with a promise.

*Why this wins:* it is the only design in the room that stays safe under the published error rates. It is honest, it is auditable, and it is what real border systems do.

### Thesis 2 — Devanagari is a weapon, not a burden

The 2026 survey documents **Script-Dependent Generative Instability**: generative models inpaint English well and non-Latin scripts badly (hallucinated Chinese characters, malformed Tamil glyphs). Devanagari is harder still — conjunct ligatures, matra placement, and a continuous shirorekha (top bar) that must join across a whole word.

**Build a Devanagari glyph-integrity forensic check:** for every Hindi/Nepali text field, verify shirorekha continuity, matra attachment geometry, conjunct well-formedness, and stroke-width consistency against the document's own font template. An AI-forged Devanagari field breaks these constraints even when the pixels look clean to a human and to a generic CNN.

*Why this wins:* it is novel, citable, cheap to implement, visually spectacular to demo, and **uniquely available to an Indian team**. No foreign vendor and no rival SIH team will have it.

### Thesis 3 — Build for the border SSB actually guards

Verified: SSB is the Lead Intelligence Agency for the **1,751 km open Indo-Nepal border**, with Passports Act powers inside a 15 km belt, where **Indians and Nepalis cross without passport or visa, tens of thousands daily**.

So the real requirements are not "scan a passport quickly". They are:

1. **Offline-first.** The device must give a full verdict in airplane mode and sync later.
2. **Devanagari + Bikram Sambat + Devanagari numerals.** A BS year is 57 (or 56) ahead of AD. Getting this wrong is a 57-year error on every Nepali date field.
3. **Handheld, not desk.** Sunlight-readable, glove-usable, one-handed, Hindi/Nepali/English UI.
4. **1:N, not 1:1.** The named threat is "multiple identities used by the same person" — that is face dedup across encounters, not photo-to-photo match.
5. **Heterogeneous documents.** Nepali citizenship certificates, voter IDs, licences — not just ICAO booklets.

*Why this wins:* a ministry jury scores domain fidelity above everything. The moment we say "Raxaul", "Rupaidiha", "Bikram Sambat", "15 km belt", and "the open border means most crossers have no travel document", the SSB officer on the panel knows we are the only team who read past the problem title.

### Thesis 4 — Use the theme correctly: blockchain for evidence, never for identity

Theme is *Blockchain & Cybersecurity*. Two ways to lose: ignore it, or bolt on "we store identities on Ethereum" (privacy-illegal under DPDP, and a theme juror will kill it).

**Correct design — no PII on chain, ever.** The ledger holds only a hash-chained, Merkle-anchored, append-only log of screening *events*: decision, model version, input digest, officer ID, timestamp, signature. That buys three real things:

- **Tamper-evident chain of custody** → the PS's own "digital trail for investigations and intelligence analysis" bullet, delivered cryptographically. Target court-admissibility under the Bharatiya Sakshya Adhiniyam electronic-records provision `[VERIFY]`.
- **A shared revocation/blacklist registry** across ICPs — a genuine distributed-ledger use case: multiple posts, intermittent connectivity, need for non-repudiation and eventual consistency.
- **ML governance** — which model version produced which decision on which input hash. Nobody at a hackathon does model provenance.

**And the cybersecurity half, done properly: we attack our own system.** The survey names **Injection Attacks** as a first-class threat — imagery supplied through upload interfaces or compromised capture streams, bypassing physical capture entirely, against which substrate-based detectors are structurally blind. We defend with capture attestation and we *show the attack working against a naive pipeline*.

### Thesis 5 — Win the room with the failure, not the success

Build an **Attack Wall**: eight forged documents we make ourselves, one per class from the published taxonomy — opportunistic (screen recapture, print, manual field edit), structure-preserving (copy-move), AI-assisted (GenAI text inpaint, face morph), injection (virtual camera), plus expired/blacklisted. Run all eight live.

Show which we catch. **Then show the one we don't**, name it, and cite why: *"composite attacks remain the most challenging across both tracks — Third Competition, 2026. We don't catch this one either. Here is what we route it to instead."*

*Why this wins:* every other team claims 99%. A team that presents its own failure case with a citation, and an architecture that stays safe despite it, is the only team the jury will still be thinking about at dinner.

---

## 3. The positioning sentence

Everything compresses to one line. Open and close with it:

> **We verify the document's cryptography first, its structure second, and its pixels last — offline, on a handheld, at an open land border where most people carry no passport at all.**

---

## 4. Scoring map — how each thesis buys marks

| SIH criterion | What we point at |
|---|---|
| Novelty / originality | Devanagari SDGI forensics; Trust Ladder fusion rule; Indian forgery benchmark with pixel masks |
| Complexity | eMRTD PA/AA chain validation; checksum-guided OCR correction; few-shot document adaptation; hash-chained ledger |
| Feasibility / practicability | Offline edge inference with a measured latency budget; few-shot adaptation to new document types with ~50 samples |
| Clarity in prescribed format | See [05-EXECUTION.md](05-EXECUTION.md) PPT outline — fill every required heading exactly |
| Scale of impact | 1,751 km, 5 states, 15 land ports; quantified queue model |
| User experience | Officer-first UI: field-level reasons, no black box, one-tap escalate, Hindi/Nepali/English |
| Sustainability / future work | Policy-as-code rule engine MHA staff can update; adapter layer for IVFRT/Interpol SLTD integration |
| Theme fit (Blockchain & Cybersecurity) | Evidence ledger + self red-teaming + injection-attack defence |

---

## 5. What we deliberately do NOT do

Saying no is how the 36 hours survives contact.

- **No claim of SOTA accuracy.** We report EER/APCER/BPCER with the operating point, and we state the generalisation gap.
- **No storing raw biometric templates.** Irreversible transforms only; no Aadhaar number stored at all.
- **No PII on any ledger.**
- **No fingerprint/iris.** Requires EAC terminal certificates we cannot obtain — say so, and show it as a designed integration point.
- **No claim of live Interpol SLTD / IVFRT / NCRB access.** Build the adapter with a documented API contract and a mock backend. Be explicit that it is mocked; never imply otherwise.
- **No 3D-mask PAD.** Out of scope; name it as a limitation.

Stating these *as deliberate scope decisions with reasons* reads as maturity. Hiding them and getting caught in Q&A is fatal.

---

## 6. The one risk that could sink us

The eMRTD NFC read is our highest-value and highest-risk feature. It needs a physically chipped passport on the demo table.

- **Mitigation A:** poll the team, mentors and families for any e-passport (any country) well before the finale.
- **Mitigation B:** stand up a software eMRTD emulator / sample SOD+DG dumps as the demo path, and label it on screen as emulated. `[VERIFY]` availability of open test data.
- **Mitigation C:** the Trust Ladder degrades gracefully — if T0 is unavailable, the system runs on T1–T3 and *says so in the UI* ("no chip present: verdict based on structural and forensic evidence only"). That degradation message is itself a good demo moment.

Decide this by the internal hackathon, not in December.
