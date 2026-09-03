# 06 — Verify Queue

Claims used in planning that are **not yet verified**. Rule: nothing here goes into the PPT, the demo narration, or a jury answer until it is cleared and its source recorded in [01-RESEARCH.md](01-RESEARCH.md).

Three of the four background research agents were terminated by an API spend limit before reporting, so items marked **[agent-gap]** are the topics that research was meant to cover.

---

## P0 — blocks the idea PPT (clear by ~5 Sept)

| # | Claim to verify | Where to look | Why it blocks |
|---|---|---|---|
| 1 | Exact SIH 2026 idea-submission template: slide count, required headings, file format | sih.gov.in via SPOC | "Clarity in the prescribed format" is a scoring criterion. Getting this wrong is how teams lose at screening |
| 2 | Official SIH 2026 evaluation rubric and weights | sih.gov.in / SPOC | Determines where to spend PPT space |
| 3 | How many teams a college may nominate per PS; whether multiple teams from one college may pick 26188 | SPOC | Affects internal-hackathon strategy |
| 4 | LPAI passenger throughput at Raxaul / Rupaidiha / Jogbani / Sunauli | lpai.gov.in statistics | The quantified impact model needs a real denominator. **Do not invent a number** |
| 5 | India e-passport rollout status and coverage in 2026 | MEA / Passport Seva / PIB | Decides whether W1 (NFC) is presented as current-fit or future-fit |

## P1 — shapes the build (clear by end Sept)

| # | Claim to verify | Notes |
|---|---|---|
| 6 | Nepali citizenship certificate: fields, script, photo, machine-readability, known forgery modes | **[agent-gap]** The single most valuable domain detail still missing |
| 7 | Devanagari numeral usage on Nepali official documents | Drives the OCR charset |
| 8 | Whether Nepal issues e-passports, and since when | Affects T0 coverage on this border |
| 9 | Bhutanese Citizenship Identity Card format | SSB also guards the Bhutan border |
| 10 | Dataset licences and download gating: IDNet, Syn-IDPASS, SIDTD, MIDV-2020, MIDV-Holo, DocXPand-25k | **[agent-gap]** Must confirm we can legally use them before building on them |
| 11 | Downloadable face-morphing datasets (FRLL-Morphs, SMDD, SYN-MAD22) and open MAD implementations | **[agent-gap]** Decides whether W5 is feasible |
| 12 | Open-weight face stack: AdaFace vs ArcFace on low-quality/aged photos; OFIQ availability; open PAD models | **[agent-gap]** Module 4 model selection |
| 13 | Devanagari/Nepali support in PaddleOCR, docTR, Surya, Tesseract `hin`/`nep` | **[agent-gap]** Module 1 model selection |
| 14 | Small VLMs viable on-device with constrained JSON output (SmolVLM2, Qwen-VL, MiniCPM-V, Florence-2) | **[agent-gap]** Structured extraction path |
| 15 | JMRTD / open eMRTD reader status, licence, Android compatibility | **[agent-gap]** W1 feasibility |
| 16 | Public eMRTD test data or emulator usable without a real chipped passport | **[agent-gap]** W1 fallback — critical |
| 17 | ICAO PKD membership in 2026; whether India participates; obtainability of CSCA master lists | Determines whether PA can chain to a real trust anchor or must use a demo CA |
| 18 | ICAO Digital Travel Credential (DTC) status 2026, Types 1/2/3 | Future-work slide credibility |

## P2 — legal and compliance (clear before the finale)

| # | Claim to verify | Notes |
|---|---|---|
| 19 | DPDP Act 2023 §17 exemptions for government/law-enforcement; status of DPDP Rules in 2026 | **[agent-gap]** |
| 20 | Aadhaar Act 2016 §29 — what may lawfully be stored | **[agent-gap]** Working assumption: never store the Aadhaar number. Confirm before any Aadhaar demo |
| 21 | Bharatiya Sakshya Adhiniyam 2023 — section governing electronic-record admissibility and the required certificate | **[agent-gap]** This is the strongest framing for the evidence ledger. Worth getting exactly right |
| 22 | Passports Act 1967 — offence and penalty sections for forged travel documents | Partially verified: SSB holds powers under this Act within a 15 km belt |
| 23 | Aadhaar Secure QR: contents, UIDAI signature, published public key, open verifiers | **[agent-gap]** Decides whether Aadhaar sits in T0 |
| 24 | DigiLocker Issued Documents API / API Setu: developer sandbox access for students | **[agent-gap]** Same |

## P3 — nice to have

| # | Claim to verify |
|---|---|
| 25 | Prior SIH problem statements on document forgery / border security, and any public solutions — establishes the baseline we must beat **[agent-gap]** |
| 26 | Existing open-source repos for "fake document detection" / "passport forgery" — confirms the commodity baseline **[agent-gap]** |
| 27 | Whether SIH juries penalise projects that ignore their theme's technology **[agent-gap]** |
| 28 | Cost and availability in India of a 365 nm UV torch and a NoIR camera module (W8) |
| 29 | Interpol SLTD: does India query it, and at how many checkpoints |
| 30 | IVFRT / Bureau of Immigration / APIS / e-FRRO scope and status **[agent-gap]** |

---

## How to clear an item

1. Find a primary source (government site, standard, official portal, peer-reviewed paper). Blogs are a last resort and must be labelled.
2. Record the claim **and its URL** in the right section of [01-RESEARCH.md](01-RESEARCH.md).
3. Delete the row here.
4. If a claim turns out **false**, that is more valuable than confirming it — update any doc that depended on it before continuing.
