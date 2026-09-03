# 01 — Research Base

All claims below trace to a source fetched on 2026-08-26. Anything unverified is tagged `[VERIFY]` and listed in [06-VERIFY-QUEUE.md](06-VERIFY-QUEUE.md). **Do not put a `[VERIFY]` claim in the PPT until it is cleared.**

---

## 1. Competition mechanics (SIH 2026)

| Fact | Value | Source |
|---|---|---|
| Edition launched | 21 Aug 2026 | [Reskilll](https://reskilll.com/blogs/smart-india-hackathon-2026-complete-guide-registration-themes-winning/) |
| Problem statements released | 226 | [SIH 2026 PS mirror](https://github.com/vedantchalke36/sih-2026-problem-statements) |
| SPOC registration | closed 31 Jul 2026 | [thenewviews](https://thenewviews.com/smart-india-hackathon/) |
| Internal college hackathon | Sept 2026 | ibid. |
| **Nomination + idea submission on portal** | **by ~30 Sept 2026** | ibid. |
| Screening of ideas | Sept–Oct 2026 | ibid. |
| Results | Oct–Nov 2026 | ibid. |
| **Grand Finale** | **Dec 2026** | ibid. |
| Team size | 6 members | [Reskilll](https://reskilll.com/blogs/sih-team-formation-how-to-build-winning-6-member-team/) |

Published evaluation dimensions (not an official weighting — treat as directional): novelty/originality, complexity, clarity and detail in the prescribed format, feasibility, practicability, sustainability, scale of impact, user experience, potential for future work. Finale scoring is described as multiple rounds, 1–20 per criterion, weighted to 100. Sources: [SIH evaluation guideline (2023)](https://www.scribd.com/document/712193023/Evaluation-Guideline-for-Smart-India-Hackathon-2023), [GDSC summary](https://medium.com/@gdsc.bitw/smart-india-hackathon-2023-introduction-and-details-idea-selection-criteria-ca2870e75d34). `[VERIFY]` exact SIH 2026 rubric and weights.

**Operational read:** ~5 weeks to the idea deadline, ~15 weeks to the finale. The idea PPT is the gate we failed last time — it is the primary deliverable now, and it is scored on *clarity in the prescribed format* as much as on novelty.

---

## 2. The state of the art is much worse than teams think

This is the single most important research finding and the backbone of our pitch.

### 2.1 Third Competition on Document Forgery Detection on ID-Cards and Passports (2026)

Organised by Hochschule Darmstadt (da/sec), Facephi, Incode, IDVC. Source: [arXiv:2607.15734](https://arxiv.org/html/2607.15734v1)

| Track | Best team | EER | BPCER10 | BPCER100 |
|---|---|---|---|---|
| Track 1 | Incode | **8.42%** | 6.01% | — |
| Track 2 (open-set) | Incode | **26.52%** | 56.53% | 75.06% |

Verbatim findings:
- *"composite attacks remain the most challenging across both tracks"*
- *"Track 2 reveals a performance gap between industrial and academic teams, likely due to access to larger proprietary datasets"*
- Several academic teams exceeded **BPCER100 > 50%** under high attack pressure.
- Baselines (Baseline-2026/2025) *"underperform relative to prior versions, suggesting instability."*

> **The world's best commercial ID-forgery detector is wrong about roughly one in four unseen documents.** Put this on a slide.

### 2.2 "From Forgeries to Foundation Models" — systematic survey (July 2026)

Source: [arXiv:2607.01442](https://arxiv.org/html/2607.01442v1) (Ramachandra et al., NTNU SAFE Center + h-da)

**Unified threat model — three attack surfaces:**
- **Presentation Attacks (PA)** — a forged, printed or screen-displayed document presented to a legitimate camera.
- **Injection Attacks (IA)** — manipulated imagery supplied through upload interfaces, compromised capture streams, software hooks, or downstream APIs, **bypassing physical capture entirely**. Detectors relying on substrate or recapture cues are structurally blind to these.
- **GenAI-driven synthesis** — full-document generation.

**Capability-driven forgery taxonomy (4 classes)** — use verbatim as our threat-model slide:

| Class | Capability barrier | Detection difficulty | Impact |
|---|---|---|---|
| Opportunistic (screen, print, manual field edit) | Low | Low–Moderate | Moderate |
| Structure-preserving (copy-move, template-aware transplant) | Moderate | Moderate | High |
| AI-assisted localised (ForgeNet-style text editing, face morph/swap) | Moderate–High, *declining* | High | Very High |
| GenAI-driven full-document | Low–Moderate | **Very High** | **Critical** |

Note the asymmetry the survey highlights: the *highest-impact* class now has one of the *lowest* capability barriers, because prompt-driven interfaces removed the skill requirement.

**The Reality Gap** (survey §5.4): models trained on private industry data significantly outperform those trained on public benchmarks. Public datasets are *"dominated by mock-ups, synthetic templates, or geographically restricted document types."* Named consequences:
- Synthetic bona fide samples cause classifiers to learn *template* features rather than liveness cues.
- Attack coverage limited to print/screen leaves models blind to digital composite, injection and GenAI attacks.
- **No public dataset carries pixel-level localisation ground truth**, so region-level detection cannot currently be evaluated at all.

**Script-Dependent Generative Instability (SDGI)** (survey §6.3): multimodal generative models inpaint English plausibly but fail on non-Latin scripts — the survey documents *"incorrect or hallucinated characters"* in Chinese and *"malformed or structurally inconsistent glyphs"* in Tamil. Its future-work section calls for multilingual coverage *"especially in view of the Script-Dependent Generative Instability."*

> **This is our opening.** Devanagari — conjuncts, matras, a continuous shirorekha — is a harder generative target than Tamil. Indian and Nepali documents are the best available substrate for exploiting SDGI, and no public dataset covers them.

### 2.3 What actually works (methods with reported numbers)

Source: survey §4.5 Table 7, [arXiv:2607.01442](https://arxiv.org/html/2607.01442v1)

| Method | Model | Key result | Named gap |
|---|---|---|---|
| Tapia & Busch 2025 | DINOv2, CLIP | EER 4.33% zero-shot | no forensic pre-training |
| Muñoz-Haro et al. 2025 | DINOv2, patch-based | **0% EER on unseen DLC-2021** | Spanish IDs only, no digital attacks |
| **Rocamora et al. 2026** | **Prototypical Nets + EfficientNetV2-B0** | **EER 3.10%, BPCER20 2.80% with only 50 identities from a new country** | screen/print attacks only |
| Zeng et al. 2026 | **SmolVLM2 (500M / 2.2B) + LoRA** | EER 0.93% Chile, 5.99% Mexico | unstable on synthetic data |
| Vidit et al. 2025 | GPT-4o vs FakeShield, SIDA | GPT-4o best on text manipulation; **fine-tuned VLMs failed to generalise** | no localisation output |

Two decisive engineering implications:

- **Few-shot prototypical networks are the right architecture for India.** There is no Indian ID forgery dataset. Rocamora shows ~50 identities of a new document type suffices for competitive performance. Our system can absorb a new Nepali citizenship-certificate revision in a day instead of a retraining cycle — an *operational* argument, not just an accuracy one.
- **A small VLM (SmolVLM2-500M) with LoRA is competitive and fits on-device.** Viable on an RTX 4060 and plausibly on a handheld.

From [arXiv:2506.05263](https://arxiv.org/html/2506.05263v1): *"Our findings indicate that bona fide images are the key to generalisation."* Also: the IJCB 2024 competition winner *"still shows a critical gap when evaluated with an unknown dataset of four different countries… there is not one universal PAD that can detect any ID card."*

### 2.4 Public datasets — what exists and what it lacks

Source: survey §5.2

| Dataset | Content | Limitation named by the survey |
|---|---|---|
| MIDV family (500 / 2019 / 2020 / Holo / LAIT) | video ID capture, multi-script OCR, hologram | all **laminated paper mock-ups**, no real security features |
| DLC2021 | lamination liveness vs print/screen | built on MIDV-2020 mock-ups; no digital or injection attacks |
| KID34K | physically manufactured plastic cards (South Korea) | geographically narrow; print/screen only |
| SIDTD | MIDV-2020 + Crop&Replace + inpainting | simple pixel-level edits, no semantic/GenAI manipulation |
| IDNet (2024) | **837,000+ images, 20 document types, 6 attack variants** | fully synthetic; no physical capture artefacts |
| Syn-IDPASS | **ICAO-9303-compliant synthetic passports**, 3 European nationalities | print/screen only, no digital edits |
| RSCID | cross-domain recapture detection | recapture only |
| FantasyID | injection-attack text manipulation | — |
| **FakeIDet-db** | **the only dataset derived from real identity documents** | — |

`[VERIFY]` licences and download gating for IDNet, Syn-IDPASS, SIDTD, MIDV-2020, DocXPand-25k before committing to any of them.

**Gap we can fill:** no public dataset has (a) Indian/Devanagari documents, or (b) pixel-level localisation masks. A small, openly-licensed, synthetic Indian-document forgery benchmark *with* masks is a genuine contribution and a defensible demo asset.

---

## 3. The cryptographic layer — what is actually provable

### 3.1 MRZ (ICAO Doc 9303)

Source: [Machine-readable passport](https://en.wikipedia.org/wiki/Machine-readable_passport)

**Check-digit algorithm (implement exactly this):**
- Character values: digits `0–9` → 0–9; letters `A–Z` → 10–35; filler `<` → 0.
- Weights cycle `7, 3, 1, 7, 3, 1, …` from the first position.
- Check digit = (Σ value × weight) mod 10.

**Formats:**

| Type | Size | MRZ layout |
|---|---|---|
| TD1 (ID-1 card, 85.6 × 54.0 mm) | credit-card | **3 rows × 30 chars** |
| TD2 (ID-2, 105.0 × 74.0 mm) | — | **2 rows × 36 chars** (31 for name, 7 personal number, one fewer check digit) |
| TD3 (passport booklet data page) | — | **2 rows × 44 chars** |
| MRV-A (visa) | 80 × 120 mm | **2 rows × 44 chars** |
| MRV-B (visa) | 74 × 105 mm | **2 rows × 36 chars** |

Charset is restricted to `A–Z`, `0–9`, `<`. Machine-readable visas are specified in **ICAO Doc 9303 Part 7** — directly relevant, since PS 26188 explicitly asks for visa number, visa type, entry validation and stay duration.

**The exploitable property:** the MRZ is a *self-checking* field. Because the charset is closed and every sub-field carries a check digit, OCR ambiguities (`0/O`, `1/I`, `5/S`, `8/B`, `2/Z`) can be resolved by searching the confusion space until the check digits validate. This converts OCR from a probabilistic step into a near-deterministic one. Almost nobody does this.

### 3.2 eMRTD chip security — precisely what each mechanism proves

Source: [Biometric passport](https://en.wikipedia.org/wiki/Biometric_passport)

| Mechanism | Proves | Does NOT prove | Mandatory? |
|---|---|---|---|
| **Passive Authentication (PA)** | Chip data is authentic and unmodified. The SOD holds hashes of every file (photo, fingerprint, …) plus a signature made with a **document signing key**, itself signed by a **country signing key**. A changed photo breaks the hash. | That the chip is genuine — **a faithful clone passes PA**. | **Yes** |
| **Active Authentication (AA)** | The chip is not a clone — it holds a private key that cannot be read or copied but whose existence is provable. | Data integrity (PA's job). | **Optional** |
| **Chip Authentication / EAC** | Chip authenticity plus reader authenticity (terminal auth); stronger crypto than BAC; gates fingerprint and iris. | — | Optional |
| **BAC / PACE** | The reader has physical access to the document (key derived from the MRZ). | Anything about authenticity. | access control |

The reader must hold trusted country signing public keys. As of Jan 2017, **55 of 60+ e-passport-issuing countries participate in the ICAO PKD**. `[VERIFY]` current PKD membership and whether India participates.

**Known attacks we must defend against — the detail that separates us from every other team:**

- **van Beek (2008):** optional security mechanisms can be disabled by *removing their presence from the passport index file* (`EF.COM`) — stripping anti-cloning (Active Authentication) from the inspection process. Documented in Doc 9303 supplement 7.
- **Calderoni et al. (2014):** AA can be bypassed by concealing `EF.COM` / `EF.SOD` metadata required by the inspection system, facilitating use of chips cloned from originals.

> **Design consequence:** never enumerate data groups from `EF.COM`. Enumerate from the signed `SOD`, and treat "AA absent" as a **red flag requiring explanation**, not a benign optional-feature skip. This is a real, published inspection-system vulnerability that our system closes — and a 30-second answer in Q&A that no other team can give.

`[VERIFY]` India's e-passport rollout status and coverage in 2026 (MEA / Passport Seva). Confirmed only that e-passports are ICAO-compliant NFC contactless smart cards, and that Bangladesh is cited as the first South Asian country to issue e-passports to all eligible citizens.

---

## 4. The operational reality at SSB's border

This section is the difference between a generic project and one an SSB officer recognises.

### 4.1 SSB's mandate

Source: [Sashastra Seema Bal](https://en.wikipedia.org/wiki/Sashastra_Seema_Bal)

- Transferred to the **Ministry of Home Affairs in 2001** under the "one border one force" concept.
- Declared **Border Guarding Force and Lead Intelligence Agency (LIA) for the Indo-Nepal border** (June 2001).
- Guards the **1,751 km Indo-Nepal border**: Uttarakhand 263.7 km (3 districts), Uttar Pradesh 599.3 km (7 districts), Bihar 800.4 km (7 districts), West Bengal 105.6 km (1 district), Sikkim. Also the Indo-Bhutan border.
- Holds police powers under the **CrPC 1973, Arms Act 1959, NDPS Act 1985 and the Passports Act 1967**, exercisable **within a 15 km belt** along the Indo-Nepal and Indo-Bhutan borders.

> Powers under the **Passports Act 1967** inside a 15 km belt mean SSB personnel are a statutory document-checking authority *away from any formal immigration counter*. That is exactly the deployment our handheld targets.

### 4.2 The border is open — this changes everything

Source: [India–Nepal border](https://en.wikipedia.org/wiki/India%E2%80%93Nepal_border)

- Length **1,751 km**; boundary from the Treaty of Sugauli (1816), current shape 1947, governed by the **1950 Indo-Nepal Treaty**.
- *"The Nepal–India border is an open border… Nepali and Indian nationals do not need passports or visas to enter each other's countries, and tens of thousands of people cross the border every day for tourism and commerce."*
- Indian side regulated by **SSB** with local police; Nepali side by the **Armed Police Force (APF)** with Nepal Police. Joint patrols occur; district officials (DM, SSB, customs, CDO, APF) meet regularly.
- **ICPs process cargo customs and immigration entry for citizens of third countries.**

**The operational truth most teams will miss:** at this border the majority of crossers present *no travel document at all*. Passport-and-visa screening applies to the third-country-national minority. The high-value detection problems are therefore:

1. A third-country national moving inside the visa-free flow.
2. A fraudulent or altered Indian/Nepali civil document used to establish identity.
3. **The same person crossing repeatedly under different identities** — a 1:N biometric problem, not a document problem. PS 26188 names this explicitly ("Multiple identities used by the same person").

### 4.3 Integrated Check Posts

Sources: [Land Ports Authority of India](https://lpai.gov.in/), [India–Nepal border](https://en.wikipedia.org/wiki/India%E2%80%93Nepal_border)

LPAI operates **15 land ports**: Attari, Agartala, Darranga, Dawki, Petrapole, **Raxaul**, **Rupaidiha**, **Jogbani**, Mankachar, Golakganj, Moreh, Sutarkandi, Srimantapur, Sabroom, and PTB at Dera Baba Nanak.

Nepal-facing ICPs to name in the pitch: **Raxaul–Birgunj (Bihar)**, **Jogbani–Biratnagar (Bihar)**, **Rupaidiha–Nepalganj (UP, ICP established 2022)**, **Sunauli/Siddharthanagar (UP, ICP established 2023)**. Pithoragarh–Dasharathchanda (Uttarakhand) is planned.

`[VERIFY]` per-ICP passenger throughput from LPAI statistics — needed for the quantified impact model.

### 4.4 Nepali document specifics

- **Bikram Sambat (Vikram Samvat) is an official calendar of Nepal.** The year count is **57 years ahead of the Gregorian calendar, except from January to March/April when it is 56 ahead**. It is lunisolar, with an intercalary month added ~7 times per 19 years (Metonic cycle). Source: [Vikram Samvat](https://en.wikipedia.org/wiki/Vikram_Samvat)

> A date-of-birth field reading `२०५०` is **not** the year 2050. Any system that does not convert BS→AD mis-computes age, expiry, and every cross-field consistency check on Nepali documents. A naive `int(year)` here produces a 57-year error. **This single check will land with an SSB jury harder than any model architecture.**

- `[VERIFY]` Nepali citizenship certificate format, fields, photo presence, machine-readability, known forgery modes.
- `[VERIFY]` whether Nepal issues e-passports and since when.
- `[VERIFY]` Devanagari numeral usage on Nepali official documents.
- `[VERIFY]` Bhutanese Citizenship Identity Card format.

---

## 5. Legal constraints

- **DPDP Act 2023** — governs digital personal data; binds *government entities* as Data Fiduciaries; establishes the Data Protection Board of India; unlike GDPR it does **not** distinguish personal from sensitive personal data and covers only *digital* personal data. Source: [DPDP Act 2023](https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Act,_2023). `[VERIFY]` §17 government/law-enforcement exemptions and the status of the DPDP Rules in 2026.
- `[VERIFY]` **Aadhaar Act 2016 §29** — restrictions on storing/sharing Aadhaar numbers and biometrics. Working assumption until verified: **never store the 12-digit Aadhaar number**; store a masked form or reference key only. Design for this from day one.
- `[VERIFY]` **Bharatiya Sakshya Adhiniyam 2023** — the section governing admissibility of electronic records (successor to Evidence Act §65B) and the certificate required. This determines whether our audit log is court-admissible, which is the strongest possible framing for the PS's "digital trail for investigations" requirement.
- **Passports Act 1967** — confirmed as a source of SSB's powers; also the offence provision for forged travel documents. `[VERIFY]` penalty sections.

---

## 6. Commercial baseline — what "good" looks like

Sources: [Regula technology](https://regulaforensics.com/explore/technologies/automatic-authenticity-control/), [Regula developer docs](https://docs.regulaforensics.com/develop/doc-reader-sdk/overview/authenticity/), [Biometric Update](https://www.biometricupdate.com/202406/regula-identity-verification-database-reaches-14k-document-templates)

Regula's document database reached **14,000 document templates**. Their authenticity control *"compares the shape, size, colour and location of such objects (patterns) with the reference ones stored in Regula Documents Database… performed in White, UV and IR lights"*, with **cross-checks of luminescent text against MRZ, barcode and visual-zone data**, at up to 2400 DPI optical resolution.

Two lessons we steal:

1. **The reference template registry is the core asset**, not the neural network — field geometry, fonts, pattern positions.
2. **Cross-zone consistency (MRZ ↔ barcode ↔ VIZ ↔ chip) is a first-class detection method** used by the industry leader. Deterministic, explainable, cheap, and it catches the most common real forgery: a forger edits the printed field and forgets the MRZ, or vice versa.

We cannot buy a multi-spectral reader. We *can* build the template registry and the cross-zone engine, and design a hardware adapter layer for UV/IR demonstrated with a cheap UV torch and a no-IR-filter camera module. `[VERIFY]` cost and availability of a 365 nm UV LED torch and a NoIR camera module in India.

---

## 7. Face layer

- **Morphing attacks** are the named frontier threat to e-passport border control: *"a malicious actor and accomplice can generate a morphed face image to obtain an e-passport, and the morphed face image can be used by both… as it can be verified against both of them."* Sources: [arXiv:2011.02045](https://arxiv.org/pdf/2011.02045), [MDPI Electronics 14(19):3851](https://www.mdpi.com/2079-9292/14/19/3851)
- **Morphing Attack Potential (MAP)** is standardised in **ISO/IEC 20059:2025**. Source: [Biometric Update, 2026](https://www.biometricupdate.com/202605/biometric-face-morph-attack-detection-breakthroughs-offer-border-security-hope)
- D-MAD (differential — document photo vs live capture) vs S-MAD (single image) is the standard split. De-morphing and similarity-score-pattern methods are active 2025–2026 research.
- PAD metrics are **APCER / BPCER / ACER** per ISO/IEC 30107-3; the competition literature reports EER, BPCER10, BPCER20, BPCER100. Use these, never "accuracy".

`[VERIFY]` open-weight model choices: AdaFace vs ArcFace for low-quality and aged document photos; OFIQ (BSI reference implementation of ISO/IEC 29794-5) availability; downloadable morphing datasets (FRLL-Morphs, SMDD, SYN-MAD22).

---

## 8. What this all means

1. Do not compete on classifier accuracy. The field's best is 26.5% EER open-set; we cannot beat that and must not pretend to.
2. Compete on **architecture, honesty and domain fidelity** — the three things a ministry jury can evaluate and a rival team cannot fake in 36 hours.
3. Our unfair advantages: **Devanagari + SDGI**, **the open-border operational model**, **cryptography-first verification**, and **a benchmark we build ourselves**.
